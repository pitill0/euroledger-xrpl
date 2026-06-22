<?php
/**
 * EuroLedger XRPL backend API client.
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Small HTTP client for the EuroLedger XRPL backend.
 */
class EuroLedger_XRPL_API_Client {
	/**
	 * Backend API base URL.
	 *
	 * @var string
	 */
	private string $api_base_url;

	/**
	 * Merchant API key.
	 *
	 * @var string
	 */
	private string $merchant_api_key;

	/**
	 * Whether debug logging is enabled.
	 *
	 * @var bool
	 */
	private bool $debug_logging;

	/**
	 * WooCommerce log source.
	 *
	 * @var string
	 */
	private string $log_source;

	/**
	 * Constructor.
	 *
	 * @param string $api_base_url Backend API base URL.
	 * @param string $merchant_api_key Merchant API key.
	 * @param bool   $debug_logging Whether debug logging is enabled.
	 * @param string $log_source WooCommerce log source.
	 */
	public function __construct(
		string $api_base_url,
		string $merchant_api_key,
		bool $debug_logging = false,
		string $log_source = 'euroledger_xrpl'
	) {
		$this->api_base_url     = untrailingslashit( $api_base_url );
		$this->merchant_api_key = $merchant_api_key;
		$this->debug_logging    = $debug_logging;
		$this->log_source       = $log_source;
	}

	/**
	 * Check backend reachability and merchant authentication.
	 *
	 * @return array<string, mixed>
	 */
	public function check_connection(): array {
		$health = $this->request( 'GET', '/health', false );

		if ( ! $health['ok'] ) {
			return array(
				'ok'      => false,
				'health'  => $health,
				'auth'    => null,
				'message' => __( 'Backend health check failed.', 'euroledger-xrpl-gateway' ),
			);
		}

		$auth = $this->request( 'GET', '/auth/me', true );

		if ( ! $auth['ok'] ) {
			return array(
				'ok'      => false,
				'health'  => $health,
				'auth'    => $auth,
				'message' => __( 'Merchant API key authentication failed.', 'euroledger-xrpl-gateway' ),
			);
		}

		return array(
			'ok'      => true,
			'health'  => $health,
			'auth'    => $auth,
			'message' => __(
				'Backend is reachable and the merchant API key is valid.',
				'euroledger-xrpl-gateway'
			),
		);
	}

	/**
	 * Create a backend payment intent.
	 *
	 * @param array<string, mixed> $payload Payment intent payload.
	 * @param string              $idempotency_key Idempotency key.
	 * @return array<string, mixed>
	 */
	public function create_payment_intent( array $payload, string $idempotency_key ): array {
		$body = wp_json_encode( $payload );

		if ( false === $body ) {
			return array(
				'ok'          => false,
				'status_code' => null,
				'body'        => null,
				'error'       => __(
					'Failed to encode payment intent payload.',
					'euroledger-xrpl-gateway'
				),
			);
		}

		return $this->request(
			'POST',
			'/payment-intents',
			true,
			array(
				'Content-Type'    => 'application/json',
				'Idempotency-Key' => $idempotency_key,
			),
			$body
		);
	}

	/**
	 * Execute an HTTP request against the backend.
	 *
	 * @param string $method HTTP method.
	 * @param string $path API path.
	 * @param bool                  $authenticated Whether to include the merchant API key.
	 * @param array<string, string> $headers Additional request headers.
	 * @param string|null           $body Request body.
	 * @return array<string, mixed>
	 */
	private function request(
		string $method,
		string $path,
		bool $authenticated,
		array $headers = array(),
		?string $body = null
	): array {
		$url = $this->api_base_url . $path;

		$args = array(
			'method'  => $method,
			'timeout' => 10,
			'headers' => array_merge(
				array(
					'Accept' => 'application/json',
				),
				$headers
			),
		);

		if ( null !== $body ) {
			$args['body'] = $body;
		}

		if ( $authenticated ) {
			$args['headers']['X-API-Key'] = $this->merchant_api_key;
		}

		$response = wp_remote_request( $url, $args );

		if ( is_wp_error( $response ) ) {
			$error_message = $response->get_error_message();
			$this->log( 'Backend request failed: ' . $error_message );

			return array(
				'ok'          => false,
				'status_code' => null,
				'body'        => null,
				'error'       => $error_message,
			);
		}

		$status_code = (int) wp_remote_retrieve_response_code( $response );
		$raw_body    = (string) wp_remote_retrieve_body( $response );
		$body        = null;

		if ( '' !== $raw_body ) {
			$decoded_body = json_decode( $raw_body, true );
			$body         = JSON_ERROR_NONE === json_last_error() ? $decoded_body : $raw_body;
		}

		return array(
			'ok'          => 200 <= $status_code && 300 > $status_code,
			'status_code' => $status_code,
			'body'        => $body,
			'error'       => null,
		);
	}

	/**
	 * Log a client message when debug logging is enabled.
	 *
	 * @param string $message Message to log.
	 */
	private function log( string $message ): void {
		if ( ! $this->debug_logging || ! function_exists( 'wc_get_logger' ) ) {
			return;
		}

		wc_get_logger()->info(
			$message,
			array(
				'source' => $this->log_source,
			)
		);
	}
}

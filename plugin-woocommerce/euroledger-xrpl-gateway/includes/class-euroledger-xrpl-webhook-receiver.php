<?php
/**
 * EuroLedger XRPL webhook receiver.
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Handles signed EuroLedger webhook events for WooCommerce orders.
 */
class EuroLedger_XRPL_Webhook_Receiver {
	private const REST_NAMESPACE = 'euroledger-xrpl/v1';
	private const REST_ROUTE     = '/webhook';
	private const OPTION_NAME    = 'woocommerce_euroledger_xrpl_settings';
	private const SIGNATURE_PREFIX = 'sha256=';

	/**
	 * Register WordPress hooks.
	 */
	public function register(): void {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
	}

	/**
	 * Register REST API routes.
	 */
	public function register_routes(): void {
		register_rest_route(
			self::REST_NAMESPACE,
			self::REST_ROUTE,
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => array( $this, 'handle_webhook' ),
				'permission_callback' => '__return_true',
			)
		);
	}

	/**
	 * Handle a signed webhook request.
	 *
	 * @param WP_REST_Request $request REST request.
	 * @return WP_REST_Response|WP_Error
	 */
	public function handle_webhook( WP_REST_Request $request ) {
		$secret = $this->get_webhook_secret();

		if ( '' === $secret ) {
			return new WP_Error(
				'euroledger_webhook_secret_missing',
				__( 'EuroLedger webhook secret is not configured.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 503 )
			);
		}

		$raw_body  = $request->get_body();
		$event     = (string) $request->get_header( 'x-euroledger-event' );
		$delivery  = (string) $request->get_header( 'x-euroledger-delivery' );
		$timestamp = (string) $request->get_header( 'x-euroledger-timestamp' );
		$signature = (string) $request->get_header( 'x-euroledger-signature' );

		if ( '' === $timestamp || '' === $signature ) {
			return new WP_Error(
				'euroledger_missing_webhook_signature_headers',
				__( 'Missing EuroLedger webhook signature headers.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 401 )
			);
		}

		if ( ! $this->is_valid_signature( $secret, $timestamp, $raw_body, $signature ) ) {
			return new WP_Error(
				'euroledger_invalid_webhook_signature',
				__( 'Invalid EuroLedger webhook signature.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 401 )
			);
		}

		$payload = json_decode( $raw_body, true );

		if ( ! is_array( $payload ) ) {
			return new WP_Error(
				'euroledger_invalid_webhook_payload',
				__( 'Invalid EuroLedger webhook payload.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 400 )
			);
		}

		$event_type = sanitize_text_field( (string) ( $payload['type'] ?? $event ) );

		switch ( $event_type ) {
			case 'payment_intent.confirmed':
				return $this->handle_payment_intent_confirmed(
					$payload,
					$delivery,
					$timestamp
				);

			case 'payment_intent.expired':
				return $this->handle_payment_intent_expired(
					$payload,
					$delivery,
					$timestamp
				);

			case 'payment_intent.cancelled':
				return $this->handle_payment_intent_cancelled(
					$payload,
					$delivery,
					$timestamp
				);

			default:
				return new WP_REST_Response(
					array(
						'ok'      => true,
						'ignored' => true,
						'event'   => $event_type,
					),
					202
				);
		}
	}

	/**
	 * Handle a payment_intent.confirmed event.
	 *
	 * @param array<string, mixed> $payload Webhook payload.
	 * @param string              $delivery Delivery id header.
	 * @param string              $timestamp Timestamp header.
	 * @return WP_REST_Response|WP_Error
	 */
	private function handle_payment_intent_confirmed(
		array $payload,
		string $delivery,
		string $timestamp
	) {
		$payment_intent = $this->extract_payment_intent( $payload );
		$intent_id      = sanitize_text_field( (string) ( $payment_intent['id'] ?? '' ) );

		if ( '' === $intent_id ) {
			return new WP_Error(
				'euroledger_missing_payment_intent_id',
				__( 'Webhook payload does not include a payment intent id.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 400 )
			);
		}

		$order = $this->find_order_by_payment_intent_id( $intent_id );

		if ( ! $order instanceof WC_Order ) {
			return new WP_Error(
				'euroledger_order_not_found',
				__( 'No WooCommerce order matches this payment intent.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 404 )
			);
		}

		$this->store_confirmed_payment_metadata(
			$order,
			$payment_intent,
			$delivery,
			$timestamp
		);

		if ( $order->has_status( 'on-hold' ) ) {
			$order->update_status(
				'processing',
				__(
					'EuroLedger XRPL payment intent confirmed by signed webhook.',
					'euroledger-xrpl-gateway'
				)
			);
		}

		$order->save();

		return new WP_REST_Response(
			array(
				'ok'       => true,
				'order_id' => $order->get_id(),
				'status'   => $order->get_status(),
			),
			200
		);
	}

	/**
	 * Handle a payment_intent.expired event.
	 *
	 * @param array<string, mixed> $payload Webhook payload.
	 * @param string              $delivery Delivery id header.
	 * @param string              $timestamp Timestamp header.
	 * @return WP_REST_Response|WP_Error
	 */
	private function handle_payment_intent_expired(
		array $payload,
		string $delivery,
		string $timestamp
	) {
		return $this->handle_terminal_payment_intent_event(
			$payload,
			$delivery,
			$timestamp,
			'payment_intent.expired',
			'expired'
		);
	}

	/**
	 * Handle a payment_intent.cancelled event.
	 *
	 * @param array<string, mixed> $payload Webhook payload.
	 * @param string              $delivery Delivery id header.
	 * @param string              $timestamp Timestamp header.
	 * @return WP_REST_Response|WP_Error
	 */
	private function handle_payment_intent_cancelled(
		array $payload,
		string $delivery,
		string $timestamp
	) {
		return $this->handle_terminal_payment_intent_event(
			$payload,
			$delivery,
			$timestamp,
			'payment_intent.cancelled',
			'cancelled'
		);
	}

	/**
	 * Handle terminal non-confirmed payment intent events.
	 *
	 * @param array<string, mixed> $payload Webhook payload.
	 * @param string              $delivery Delivery id header.
	 * @param string              $timestamp Timestamp header.
	 * @param string              $event_type Event type.
	 * @param string              $status Payment intent status.
	 * @return WP_REST_Response|WP_Error
	 */
	private function handle_terminal_payment_intent_event(
		array $payload,
		string $delivery,
		string $timestamp,
		string $event_type,
		string $status
	) {
		$payment_intent = $this->extract_payment_intent( $payload );
		$intent_id      = sanitize_text_field( (string) ( $payment_intent['id'] ?? '' ) );

		if ( '' === $intent_id ) {
			return new WP_Error(
				'euroledger_missing_payment_intent_id',
				__( 'Webhook payload does not include a payment intent id.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 400 )
			);
		}

		$order = $this->find_order_by_payment_intent_id( $intent_id );

		if ( ! $order instanceof WC_Order ) {
			return new WP_Error(
				'euroledger_order_not_found',
				__( 'No WooCommerce order matches this payment intent.', 'euroledger-xrpl-gateway' ),
				array( 'status' => 404 )
			);
		}

		$previous_euroledger_status = trim(
			(string) $order->get_meta( '_euroledger_payment_intent_status' )
		);

		$this->store_terminal_payment_metadata(
			$order,
			$payment_intent,
			$delivery,
			$timestamp,
			$event_type,
			$status
		);

		if ( $order->has_status( 'on-hold' ) ) {
			$order->update_status(
				'cancelled',
				$this->build_terminal_order_note( $status, $payment_intent )
			);
		} elseif ( $previous_euroledger_status !== $status ) {
			$order->add_order_note(
				$this->build_terminal_order_note( $status, $payment_intent )
			);
		}

		$order->save();

		return new WP_REST_Response(
			array(
				'ok'       => true,
				'order_id' => $order->get_id(),
				'status'   => $order->get_status(),
			),
			200
		);
	}

	/**
	 * Validate a webhook signature.
	 *
	 * @param string $secret Webhook secret.
	 * @param string $timestamp Timestamp header.
	 * @param string $raw_body Raw request body.
	 * @param string $signature Signature header.
	 * @return bool
	 */
	private function is_valid_signature(
		string $secret,
		string $timestamp,
		string $raw_body,
		string $signature
	): bool {
		if ( '' === $timestamp || '' === $signature || ! ctype_digit( $timestamp ) ) {
			return false;
		}

		$signed_payload     = $timestamp . '.' . $raw_body;
		$expected_signature = self::SIGNATURE_PREFIX . hash_hmac(
			'sha256',
			$signed_payload,
			$secret
		);

		return hash_equals( $expected_signature, $signature );
	}

	/**
	 * Extract the payment intent object from the event payload.
	 *
	 * @param array<string, mixed> $payload Webhook payload.
	 * @return array<string, mixed>
	 */
	private function extract_payment_intent( array $payload ): array {
		$data = $payload['data'] ?? null;

		if ( ! is_array( $data ) ) {
			return array();
		}

		$object = $data['object'] ?? null;

		return is_array( $object ) ? $object : array();
	}

	/**
	 * Locate a WooCommerce order by EuroLedger payment intent id.
	 *
	 * @param string $intent_id Payment intent id.
	 * @return WC_Order|null
	 */
	private function find_order_by_payment_intent_id( string $intent_id ): ?WC_Order {
		$orders = wc_get_orders(
			array(
				'limit'      => 1,
				'meta_key'   => '_euroledger_payment_intent_id',
				'meta_value' => $intent_id,
				'return'     => 'objects',
			)
		);

		$order = $orders[0] ?? null;

		return $order instanceof WC_Order ? $order : null;
	}

	/**
	 * Store confirmed payment metadata on the order.
	 *
	 * @param WC_Order             $order WooCommerce order.
	 * @param array<string, mixed> $payment_intent Payment intent payload.
	 * @param string               $delivery Delivery id header.
	 * @param string               $timestamp Timestamp header.
	 */
	private function store_confirmed_payment_metadata(
		WC_Order $order,
		array $payment_intent,
		string $delivery,
		string $timestamp
	): void {
		$order->update_meta_data( '_euroledger_payment_intent_status', 'confirmed' );
		$order->update_meta_data(
			'_euroledger_payment_intent_confirmed_at',
			sanitize_text_field( (string) ( $payment_intent['confirmed_at'] ?? gmdate( 'c' ) ) )
		);
		$order->update_meta_data(
			'_euroledger_webhook_last_event',
			'payment_intent.confirmed'
		);
		$order->update_meta_data(
			'_euroledger_webhook_last_delivery_id',
			sanitize_text_field( $delivery )
		);
		$order->update_meta_data(
			'_euroledger_webhook_last_timestamp',
			sanitize_text_field( $timestamp )
		);

		$transaction_hash = (string) ( $payment_intent['xrpl_transaction_hash'] ?? '' );

		if ( '' !== $transaction_hash ) {
			$order->update_meta_data(
				'_euroledger_xrpl_transaction_hash',
				sanitize_text_field( $transaction_hash )
			);
		}

		$reference = (string) ( $payment_intent['reference'] ?? '' );

		if ( '' !== $reference ) {
			$order->update_meta_data(
				'_euroledger_payment_intent_reference',
				sanitize_text_field( $reference )
			);
		}
	}


	/**
	 * Store terminal payment metadata on the order.
	 *
	 * @param WC_Order             $order WooCommerce order.
	 * @param array<string, mixed> $payment_intent Payment intent payload.
	 * @param string               $delivery Delivery id header.
	 * @param string               $timestamp Timestamp header.
	 * @param string               $event_type Event type.
	 * @param string               $status Payment intent status.
	 */
	private function store_terminal_payment_metadata(
		WC_Order $order,
		array $payment_intent,
		string $delivery,
		string $timestamp,
		string $event_type,
		string $status
	): void {
		$order->update_meta_data( '_euroledger_payment_intent_status', $status );
		$order->update_meta_data(
			'_euroledger_webhook_last_event',
			sanitize_text_field( $event_type )
		);
		$order->update_meta_data(
			'_euroledger_webhook_last_delivery_id',
			sanitize_text_field( $delivery )
		);
		$order->update_meta_data(
			'_euroledger_webhook_last_timestamp',
			sanitize_text_field( $timestamp )
		);

		$reference = (string) ( $payment_intent['reference'] ?? '' );

		if ( '' !== $reference ) {
			$order->update_meta_data(
				'_euroledger_payment_intent_reference',
				sanitize_text_field( $reference )
			);
		}

		$expires_at = (string) ( $payment_intent['expires_at'] ?? '' );

		if ( '' !== $expires_at ) {
			$order->update_meta_data(
				'_euroledger_payment_intent_expires_at',
				sanitize_text_field( $expires_at )
			);
		}

		$cancelled_at = (string) ( $payment_intent['cancelled_at'] ?? '' );

		if ( '' !== $cancelled_at ) {
			$order->update_meta_data(
				'_euroledger_payment_intent_cancelled_at',
				sanitize_text_field( $cancelled_at )
			);
		}

		$cancellation_reason = (string) ( $payment_intent['cancellation_reason'] ?? '' );

		if ( '' !== $cancellation_reason ) {
			$order->update_meta_data(
				'_euroledger_payment_intent_cancellation_reason',
				sanitize_text_field( $cancellation_reason )
			);
		}
	}

	/**
	 * Build an order note for terminal payment intent events.
	 *
	 * @param string              $status Payment intent status.
	 * @param array<string, mixed> $payment_intent Payment intent payload.
	 * @return string
	 */
	private function build_terminal_order_note( string $status, array $payment_intent ): string {
		if ( 'expired' === $status ) {
			return __(
				'EuroLedger XRPL payment intent expired before confirmation.',
				'euroledger-xrpl-gateway'
			);
		}

		$reason = trim( (string) ( $payment_intent['cancellation_reason'] ?? '' ) );

		if ( '' === $reason ) {
			return __(
				'EuroLedger XRPL payment intent was cancelled.',
				'euroledger-xrpl-gateway'
			);
		}

		return sprintf(
			/* translators: %s: payment intent cancellation reason. */
			__( 'EuroLedger XRPL payment intent was cancelled. Reason: %s', 'euroledger-xrpl-gateway' ),
			sanitize_text_field( $reason )
		);
	}

	/**
	 * Get the configured webhook secret.
	 *
	 * @return string
	 */
	private function get_webhook_secret(): string {
		$settings = get_option( self::OPTION_NAME, array() );

		if ( ! is_array( $settings ) ) {
			return '';
		}

		return trim( (string) ( $settings['webhook_secret'] ?? '' ) );
	}
}

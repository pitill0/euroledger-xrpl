<?php
/**
 * WooCommerce gateway class for EuroLedger XRPL.
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Experimental EuroLedger XRPL payment gateway.
 */
class WC_Gateway_EuroLedger_XRPL extends WC_Payment_Gateway {
	/**
	 * API base URL.
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
	 * Test mode flag.
	 *
	 * @var bool
	 */
	private bool $test_mode;

	/**
	 * Debug logging flag.
	 *
	 * @var bool
	 */
	private bool $debug_logging;

	/**
	 * Constructor.
	 */
	public function __construct() {
		$this->id                 = 'euroledger_xrpl';
		$this->method_title       = __( 'EuroLedger XRPL', 'euroledger-xrpl-gateway' );
		$this->method_description = __(
			'Experimental EuroLedger XRPL payment gateway.',
			'euroledger-xrpl-gateway'
		);
		$this->has_fields         = false;
		$this->supports           = array(
			'products',
		);

		$this->init_form_fields();
		$this->init_settings();
		$this->load_settings();

		add_action(
			'woocommerce_update_options_payment_gateways_' . $this->id,
			array( $this, 'process_admin_options' )
		);
	}

	/**
	 * Define admin settings fields.
	 */
	public function init_form_fields() {
		$this->form_fields = array(
			'enabled'          => array(
				'title'       => __( 'Enable/Disable', 'euroledger-xrpl-gateway' ),
				'type'        => 'checkbox',
				'label'       => __( 'Enable EuroLedger XRPL', 'euroledger-xrpl-gateway' ),
				'default'     => 'no',
				'description' => __(
					'Keep disabled until the backend integration block is implemented.',
					'euroledger-xrpl-gateway'
				),
			),
			'title'            => array(
				'title'       => __( 'Title', 'euroledger-xrpl-gateway' ),
				'type'        => 'text',
				'default'     => __( 'EuroLedger XRPL', 'euroledger-xrpl-gateway' ),
				'description' => __(
					'Payment method title shown at checkout.',
					'euroledger-xrpl-gateway'
				),
				'desc_tip'    => true,
			),
			'description'      => array(
				'title'       => __( 'Description', 'euroledger-xrpl-gateway' ),
				'type'        => 'textarea',
				'default'     => __(
					'Pay using a EuroLedger XRPL testnet payment intent.',
					'euroledger-xrpl-gateway'
				),
				'description' => __(
					'Payment method description shown at checkout.',
					'euroledger-xrpl-gateway'
				),
				'desc_tip'    => true,
			),
			'api_base_url'     => array(
				'title'       => __( 'API base URL', 'euroledger-xrpl-gateway' ),
				'type'        => 'url',
				'default'     => 'http://localhost:8000',
				'description' => __(
					'Base URL of the EuroLedger XRPL backend API.',
					'euroledger-xrpl-gateway'
				),
				'desc_tip'    => true,
			),
			'merchant_api_key' => array(
				'title'       => __( 'Merchant API key', 'euroledger-xrpl-gateway' ),
				'type'        => 'password',
				'default'     => '',
				'description' => __(
					'API key used to authenticate this WooCommerce merchant.',
					'euroledger-xrpl-gateway'
				),
				'desc_tip'    => true,
			),
			'test_mode'        => array(
				'title'       => __( 'Test mode', 'euroledger-xrpl-gateway' ),
				'type'        => 'checkbox',
				'label'       => __( 'Use testnet/test backend flows', 'euroledger-xrpl-gateway' ),
				'default'     => 'yes',
				'description' => __(
					'This gateway is experimental and should remain in test mode.',
					'euroledger-xrpl-gateway'
				),
			),
			'debug_logging'    => array(
				'title'       => __( 'Debug logging', 'euroledger-xrpl-gateway' ),
				'type'        => 'checkbox',
				'label'       => __( 'Enable WooCommerce gateway logs', 'euroledger-xrpl-gateway' ),
				'default'     => 'no',
				'description' => __(
					'Do not log secrets or full customer payloads.',
					'euroledger-xrpl-gateway'
				),
			),
		);
	}

	/**
	 * Load settings into typed properties.
	 */
	private function load_settings(): void {
		$this->title            = $this->get_option( 'title', 'EuroLedger XRPL' );
		$this->description      = $this->get_option( 'description', '' );
		$this->enabled          = $this->get_option( 'enabled', 'no' );
		$this->api_base_url     = untrailingslashit(
			$this->get_option( 'api_base_url', 'http://localhost:8000' )
		);
		$this->merchant_api_key = $this->get_option( 'merchant_api_key', '' );
		$this->test_mode        = 'yes' === $this->get_option( 'test_mode', 'yes' );
		$this->debug_logging    = 'yes' === $this->get_option( 'debug_logging', 'no' );
	}

	/**
	 * Validate required settings.
	 *
	 * @return bool
	 */
	public function is_available() {
		if ( 'yes' !== $this->enabled ) {
			return false;
		}

		if ( '' === $this->api_base_url || '' === $this->merchant_api_key ) {
			return false;
		}

		return parent::is_available();
	}

	/**
	 * Process a checkout payment.
	 *
	 * Payment intent creation is intentionally deferred to the next block.
	 *
	 * @param int $order_id WooCommerce order id.
	 * @return array<string, string>
	 */
	public function process_payment( $order_id ) {
		$this->log(
			sprintf(
				'Checkout attempted before backend integration. order_id=%d',
				(int) $order_id
			)
		);

		wc_add_notice(
			__(
				'EuroLedger XRPL checkout integration is not available yet.',
				'euroledger-xrpl-gateway'
			),
			'error'
		);

		return array(
			'result' => 'failure',
		);
	}

	/**
	 * Log a gateway message when debug logging is enabled.
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
				'source' => $this->id,
			)
		);
	}

	/**
	 * Expose sanitized configuration for future tests.
	 *
	 * @return array<string, bool|string>
	 */
	public function get_euroledger_config(): array {
		return array(
			'api_base_url'  => $this->api_base_url,
			'test_mode'     => $this->test_mode,
			'debug_logging' => $this->debug_logging,
			'has_api_key'   => '' !== $this->merchant_api_key,
		);
	}
}

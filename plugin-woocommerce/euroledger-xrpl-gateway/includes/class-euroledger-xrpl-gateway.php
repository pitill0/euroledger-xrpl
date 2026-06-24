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
		add_action(
			'woocommerce_thankyou_' . $this->id,
			array( $this, 'render_payment_instructions' )
		);
		add_action(
			'woocommerce_order_details_before_order_table',
			array( $this, 'render_payment_instructions' )
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

			'webhook_secret'  => array(
				'title'       => __( 'Webhook secret', 'euroledger-xrpl-gateway' ),
				'type'        => 'password',
				'default'     => '',
				'description' => __(
					'Secret used to verify signed EuroLedger webhook deliveries sent to WordPress.',
					'euroledger-xrpl-gateway'
				),
				'desc_tip'    => true,
			),
			'dashboard_base_url' => array(
				'title'       => __( 'Dashboard base URL', 'euroledger-xrpl-gateway' ),
				'type'        => 'url',
				'default'     => '',
				'description' => __(
					'Optional EuroLedger dashboard URL used to link payment intents from WooCommerce orders.',
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
			'connection_check' => array(
				'title' => __( 'Backend connection', 'euroledger-xrpl-gateway' ),
				'type'  => 'connection_check',
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
	 * Creates a backend payment intent, stores its identifiers on the order and
	 * keeps the order on hold until an external payment confirmation arrives.
	 *
	 * @param int $order_id WooCommerce order id.
	 * @return array<string, string>
	 */
	public function process_payment( $order_id ) {
		$order = wc_get_order( $order_id );

		if ( ! $order instanceof WC_Order ) {
			wc_add_notice(
				__( 'Unable to load the WooCommerce order.', 'euroledger-xrpl-gateway' ),
				'error'
			);

			return array(
				'result' => 'failure',
			);
		}

		$existing_intent_id = (string) $order->get_meta( '_euroledger_payment_intent_id' );

		if ( '' !== $existing_intent_id ) {
			$this->log(
				sprintf(
					'Reusing existing payment intent. order_id=%d payment_intent_id=%s',
					(int) $order_id,
					$existing_intent_id
				)
			);

			return $this->payment_success_redirect( $order );
		}

		$client = new EuroLedger_XRPL_API_Client(
			$this->api_base_url,
			$this->merchant_api_key,
			$this->debug_logging,
			$this->id
		);

		$payload         = $this->build_payment_intent_payload( $order );
		$idempotency_key = $this->build_payment_intent_idempotency_key( $order );
		$result          = $client->create_payment_intent( $payload, $idempotency_key );

		if ( ! $result['ok'] || ! is_array( $result['body'] ) ) {
			$this->log(
				sprintf(
					'Payment intent creation failed. order_id=%d status=%s error=%s',
					(int) $order_id,
					(string) ( $result['status_code'] ?? 'n/a' ),
					(string) ( $result['error'] ?? 'unknown' )
				)
			);

			wc_add_notice(
				__(
					'EuroLedger XRPL could not create a payment intent. Please try again.',
					'euroledger-xrpl-gateway'
				),
				'error'
			);

			return array(
				'result' => 'failure',
			);
		}

		$this->store_payment_intent_on_order( $order, $result['body'] );

		$order->update_status(
			'on-hold',
			__(
				'EuroLedger XRPL payment intent created. Awaiting external payment confirmation.',
				'euroledger-xrpl-gateway'
			)
		);
		$order->save();

		WC()->cart->empty_cart();

		return $this->payment_success_redirect( $order );
	}

	/**
	 * Build backend payment intent payload from a WooCommerce order.
	 *
	 * @param WC_Order $order WooCommerce order.
	 * @return array<string, mixed>
	 */
	private function build_payment_intent_payload( WC_Order $order ): array {
		return array(
			'amount'             => wc_format_decimal( $order->get_total(), 2 ),
			'currency'           => $order->get_currency(),
			'description'        => sprintf(
				'WooCommerce order #%s',
				$order->get_order_number()
			),
			'expires_in_seconds' => 900,
		);
	}

	/**
	 * Build a stable idempotency key for payment intent creation.
	 *
	 * @param WC_Order $order WooCommerce order.
	 * @return string
	 */
	private function build_payment_intent_idempotency_key( WC_Order $order ): string {
		return sprintf(
			'woocommerce-order-%d-payment-intent',
			$order->get_id()
		);
	}

	/**
	 * Store backend payment intent metadata on the WooCommerce order.
	 *
	 * @param WC_Order            $order WooCommerce order.
	 * @param array<string, mixed> $payment_intent Payment intent response body.
	 */
	private function store_payment_intent_on_order(
		WC_Order $order,
		array $payment_intent
	): void {
		$order->update_meta_data(
			'_euroledger_payment_intent_id',
			sanitize_text_field( (string) ( $payment_intent['id'] ?? '' ) )
		);
		$order->update_meta_data(
			'_euroledger_payment_intent_reference',
			sanitize_text_field( (string) ( $payment_intent['reference'] ?? '' ) )
		);
		$order->update_meta_data(
			'_euroledger_payment_intent_status',
			sanitize_text_field( (string) ( $payment_intent['status'] ?? '' ) )
		);
		$order->update_meta_data(
			'_euroledger_payment_intent_created_at',
			sanitize_text_field( (string) ( $payment_intent['created_at'] ?? '' ) )
		);
	}

	/**
	 * Build the standard WooCommerce success redirect response.
	 *
	 * @param WC_Order $order WooCommerce order.
	 * @return array<string, string>
	 */
	private function payment_success_redirect( WC_Order $order ): array {
		return array(
			'result'   => 'success',
			'redirect' => $this->get_return_url( $order ),
		);
	}

	/**
	 * Render customer-facing EuroLedger payment status.
	 *
	 * This appears on the order received page and in My account > Orders.
	 * The thank-you and order-details hooks can both run on the same page, so
	 * rendering is guarded per order id to avoid duplicate blocks.
	 *
	 * @param int|WC_Order $order_or_id WooCommerce order id or order object.
	 */
	public function render_payment_instructions( $order_or_id ): void {
		static $rendered_order_ids = array();

		$order = $order_or_id instanceof WC_Order ? $order_or_id : wc_get_order( $order_or_id );

		if ( ! $order instanceof WC_Order ) {
			return;
		}

		$order_id = (int) $order->get_id();

		if ( isset( $rendered_order_ids[ $order_id ] ) ) {
			return;
		}

		if ( $this->id !== $order->get_payment_method() ) {
			return;
		}

		$payment_intent_id = trim( (string) $order->get_meta( '_euroledger_payment_intent_id' ) );
		$reference         = trim( (string) $order->get_meta( '_euroledger_payment_intent_reference' ) );

		if ( '' === $payment_intent_id && '' === $reference ) {
			return;
		}

		$rendered_order_ids[ $order_id ] = true;

		$status              = trim( (string) $order->get_meta( '_euroledger_payment_intent_status' ) );
		$xrpl_hash           = trim( (string) $order->get_meta( '_euroledger_xrpl_transaction_hash' ) );
		$cancellation_reason = trim( (string) $order->get_meta( '_euroledger_payment_intent_cancellation_reason' ) );

		$this->render_customer_payment_status_assets();

		echo '<section class="woocommerce-order-details euroledger-xrpl-customer-status" aria-label="' . esc_attr__( 'EuroLedger XRPL payment status', 'euroledger-xrpl-gateway' ) . '">';
		echo '<div class="euroledger-xrpl-customer-status__header">';
		echo '<div>';
		echo '<h2>' . esc_html__( 'EuroLedger XRPL payment', 'euroledger-xrpl-gateway' ) . '</h2>';
		echo '<p>' . esc_html( $this->get_customer_status_message( $status ) ) . '</p>';
		echo '</div>';
		echo $this->render_customer_status_badge( $status );
		echo '</div>';

		echo '<dl class="euroledger-xrpl-customer-status__details">';
		$this->render_customer_status_row(
			__( 'Payment reference', 'euroledger-xrpl-gateway' ),
			$reference,
			true
		);
		$this->render_customer_status_row(
			__( 'Payment intent ID', 'euroledger-xrpl-gateway' ),
			$payment_intent_id,
			false
		);
		$this->render_customer_status_row(
			__( 'XRPL transaction hash', 'euroledger-xrpl-gateway' ),
			$xrpl_hash,
			false
		);
		$this->render_customer_status_row(
			__( 'Cancellation reason', 'euroledger-xrpl-gateway' ),
			$cancellation_reason,
			false
		);
		echo '</dl>';

		if ( 'pending' === strtolower( $status ) && '' !== $reference ) {
			echo '<p class="euroledger-xrpl-customer-status__hint">';
			echo esc_html__( 'Use the payment reference as the XRPL memo/reference when sending the payment. The order will update automatically after confirmation.', 'euroledger-xrpl-gateway' );
			echo '</p>';
		}

		echo '</section>';
	}

	/**
	 * Return a customer-facing status message.
	 *
	 * @param string $status Payment intent status.
	 * @return string
	 */
	private function get_customer_status_message( string $status ): string {
		switch ( strtolower( trim( $status ) ) ) {
			case 'confirmed':
				return __( 'Payment confirmed. Your order is now being processed.', 'euroledger-xrpl-gateway' );
			case 'cancelled':
				return __( 'This payment intent has been cancelled. The order is no longer awaiting this payment.', 'euroledger-xrpl-gateway' );
			case 'expired':
				return __( 'This payment intent has expired. The order is no longer awaiting this payment.', 'euroledger-xrpl-gateway' );
			case 'pending':
			default:
				return __( 'Your payment intent is pending. Send the XRPL payment using the reference below and wait for automatic confirmation.', 'euroledger-xrpl-gateway' );
		}
	}

	/**
	 * Render one customer-facing status row when a value exists.
	 *
	 * @param string $label Field label.
	 * @param string $value Field value.
	 * @param bool   $highlight Whether the row should be visually highlighted.
	 */
	private function render_customer_status_row( string $label, string $value, bool $highlight ): void {
		if ( '' === $value ) {
			return;
		}

		$classes = 'euroledger-xrpl-customer-status__value';

		if ( $highlight ) {
			$classes .= ' euroledger-xrpl-customer-status__value--highlight';
		}

		echo '<dt>' . esc_html( $label ) . '</dt>';
		echo '<dd><code class="' . esc_attr( $classes ) . '">' . esc_html( $value ) . '</code></dd>';
	}

	/**
	 * Render customer-facing payment status badge.
	 *
	 * @param string $status Payment intent status.
	 * @return string
	 */
	private function render_customer_status_badge( string $status ): string {
		$normalized_status = sanitize_html_class( strtolower( trim( $status ) ) );
		$known_statuses    = array( 'pending', 'confirmed', 'expired', 'cancelled' );

		if ( '' === $normalized_status || ! in_array( $normalized_status, $known_statuses, true ) ) {
			$normalized_status = 'unknown';
		}

		$label = '' === $status ? __( 'Unknown', 'euroledger-xrpl-gateway' ) : $status;

		return sprintf(
			'<span class="euroledger-xrpl-customer-status__badge euroledger-xrpl-customer-status__badge--%1$s">%2$s</span>',
			esc_attr( $normalized_status ),
			esc_html( $label )
		);
	}

	/**
	 * Render inline assets for the customer-facing payment status block.
	 */
	private function render_customer_payment_status_assets(): void {
		static $rendered = false;

		if ( $rendered ) {
			return;
		}

		$rendered = true;
		?>
		<style>
			.euroledger-xrpl-customer-status {
				border: 1px solid #dcdcde;
				border-radius: 8px;
				margin: 0 0 24px;
				overflow: hidden;
			}
			.euroledger-xrpl-customer-status__header {
				align-items: flex-start;
				background: #f6f7f7;
				display: flex;
				gap: 16px;
				justify-content: space-between;
				padding: 18px 20px;
			}
			.euroledger-xrpl-customer-status__header h2 {
				margin: 0 0 6px;
			}
			.euroledger-xrpl-customer-status__header p {
				margin: 0;
			}
			.euroledger-xrpl-customer-status__badge {
				border-radius: 999px;
				display: inline-flex;
				font-size: 12px;
				font-weight: 700;
				line-height: 1;
				padding: 7px 10px;
				text-transform: uppercase;
				white-space: nowrap;
			}
			.euroledger-xrpl-customer-status__badge--confirmed { background: #d1e7dd; color: #0f5132; }
			.euroledger-xrpl-customer-status__badge--pending { background: #fff3cd; color: #664d03; }
			.euroledger-xrpl-customer-status__badge--expired,
			.euroledger-xrpl-customer-status__badge--cancelled { background: #f8d7da; color: #842029; }
			.euroledger-xrpl-customer-status__badge--unknown { background: #e2e3e5; color: #41464b; }
			.euroledger-xrpl-customer-status__details {
				display: grid;
				grid-template-columns: minmax(160px, 240px) minmax(0, 1fr);
				margin: 0;
			}
			.euroledger-xrpl-customer-status__details dt,
			.euroledger-xrpl-customer-status__details dd {
				border-top: 1px solid #f0f0f1;
				margin: 0;
				padding: 12px 20px;
			}
			.euroledger-xrpl-customer-status__details dt {
				font-weight: 700;
			}
			.euroledger-xrpl-customer-status__value {
				background: #f6f7f7;
				border-radius: 4px;
				display: inline-block;
				max-width: 100%;
				overflow-wrap: anywhere;
				padding: 4px 6px;
			}
			.euroledger-xrpl-customer-status__value--highlight {
				font-size: 1.05em;
				font-weight: 700;
			}
			.euroledger-xrpl-customer-status__hint {
				border-top: 1px solid #f0f0f1;
				margin: 0;
				padding: 14px 20px;
			}
			@media (max-width: 782px) {
				.euroledger-xrpl-customer-status__header {
					flex-direction: column;
				}
				.euroledger-xrpl-customer-status__details {
					grid-template-columns: 1fr;
				}
				.euroledger-xrpl-customer-status__details dt {
					padding-bottom: 0;
				}
				.euroledger-xrpl-customer-status__details dd {
					border-top: 0;
					padding-top: 6px;
				}
			}
		</style>
		<?php
	}

	/**
	 * Render the backend connection check admin field.
	 *
	 * @param string $key Field key.
	 * @param array<string, mixed> $data Field data.
	 * @return string
	 */
	public function generate_connection_check_html( $key, $data ) {
		$field_key = $this->get_field_key( $key );
		$defaults  = array(
			'title' => '',
		);
		$data      = wp_parse_args( $data, $defaults );

		$check_url = wp_nonce_url(
			add_query_arg(
				array(
					'page'                               => 'wc-settings',
					'tab'                                => 'checkout',
					'section'                            => $this->id,
					'euroledger_xrpl_check_connection' => '1',
				),
				admin_url( 'admin.php' )
			),
			'euroledger_xrpl_check_connection_' . $this->id
		);

		$html  = '<tr valign="top">';
		$html .= '<th scope="row" class="titledesc">';
		$html .= '<label for="' . esc_attr( $field_key ) . '">';
		$html .= esc_html( $data['title'] );
		$html .= '</label></th>';
		$html .= '<td class="forminp">';
		$html .= $this->render_connection_check_status();
		$html .= '<p><a class="button" href="' . esc_url( $check_url ) . '">';
		$html .= esc_html__( 'Check backend connection', 'euroledger-xrpl-gateway' );
		$html .= '</a></p>';
		$html .= '<p class="description">';
		$html .= esc_html__(
			'Checks /health and validates the configured merchant API key with /auth/me.',
			'euroledger-xrpl-gateway'
		);
		$html .= '</p>';
		$html .= '</td></tr>';

		return $html;
	}

	/**
	 * Render the latest connection check result for the settings screen.
	 *
	 * @return string
	 */
	private function render_connection_check_status(): string {
		$result = $this->maybe_check_backend_connection();

		if ( null === $result ) {
			return '<p>' . esc_html__(
				'Backend connection has not been checked in this page load.',
				'euroledger-xrpl-gateway'
			) . '</p>';
		}

		$notice_class = $result['ok'] ? 'notice-success' : 'notice-error';
		$html         = '<div class="notice inline ' . esc_attr( $notice_class ) . '"><p>';
		$html        .= esc_html( $result['message'] );
		$html        .= '</p>';
		$html        .= '<ul>';
		$health_status = $this->format_check_step( 'Health', $result['health'] );
		$html         .= '<li>' . esc_html( $health_status ) . '</li>';

		if ( null !== $result['auth'] ) {
			$auth_status = $this->format_check_step( 'Authentication', $result['auth'] );
			$html       .= '<li>' . esc_html( $auth_status ) . '</li>';
		}

		$html .= '</ul></div>';

		return $html;
	}

	/**
	 * Run a backend connection check when explicitly requested by an admin.
	 *
	 * @return array<string, mixed>|null
	 */
	private function maybe_check_backend_connection(): ?array {
		if ( empty( $_GET['euroledger_xrpl_check_connection'] ) ) {
			return null;
		}

		if ( ! current_user_can( 'manage_woocommerce' ) ) {
			return array(
				'ok'      => false,
				'health'  => null,
				'auth'    => null,
				'message' => __(
					'You do not have permission to check this connection.',
					'euroledger-xrpl-gateway'
				),
			);
		}

		check_admin_referer( 'euroledger_xrpl_check_connection_' . $this->id );

		if ( '' === $this->api_base_url ) {
			return array(
				'ok'      => false,
				'health'  => null,
				'auth'    => null,
				'message' => __(
					'Configure the API base URL before checking the connection.',
					'euroledger-xrpl-gateway'
				),
			);
		}

		if ( '' === $this->merchant_api_key ) {
			return array(
				'ok'      => false,
				'health'  => null,
				'auth'    => null,
				'message' => __(
					'Configure the merchant API key before checking the connection.',
					'euroledger-xrpl-gateway'
				),
			);
		}

		$client = new EuroLedger_XRPL_API_Client(
			$this->api_base_url,
			$this->merchant_api_key,
			$this->debug_logging,
			$this->id
		);

		return $client->check_connection();
	}

	/**
	 * Format a single connection check step for display.
	 *
	 * @param string $label Step label.
	 * @param array<string, mixed>|null $result Step result.
	 * @return string
	 */
	private function format_check_step( string $label, ?array $result ): string {
		if ( null === $result ) {
			return sprintf( '%s: not checked', $label );
		}

		$status_code = null === $result['status_code']
			? 'n/a'
			: (string) $result['status_code'];

		if ( $result['ok'] ) {
			return sprintf( '%s: OK (HTTP %s)', $label, $status_code );
		}

		$error = $result['error'] ?? 'HTTP ' . $status_code;

		return sprintf( '%s: failed (%s)', $label, $error );
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

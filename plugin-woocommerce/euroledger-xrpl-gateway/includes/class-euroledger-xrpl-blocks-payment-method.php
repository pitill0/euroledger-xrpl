<?php
/**
 * WooCommerce Checkout Blocks integration for EuroLedger XRPL.
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Register EuroLedger XRPL as a Blocks checkout payment method.
 */
final class EuroLedger_XRPL_Blocks_Payment_Method extends \Automattic\WooCommerce\Blocks\Payments\Integrations\AbstractPaymentMethodType {
	/**
	 * Payment method name. Must match the classic gateway id.
	 *
	 * @var string
	 */
	protected $name = 'euroledger_xrpl';

	/**
	 * Initialize settings for the Blocks payment method.
	 */
	public function initialize(): void {
		$this->settings = get_option( 'woocommerce_euroledger_xrpl_settings', array() );
	}

	/**
	 * Return whether the payment method should be visible in Checkout Blocks.
	 *
	 * @return bool
	 */
	public function is_active(): bool {
		return 'yes' === $this->get_gateway_setting( 'enabled', 'no' )
			&& $this->has_required_checkout_configuration();
	}

	/**
	 * Return script handles required by the Blocks payment method.
	 *
	 * @return array<int, string>
	 */
	public function get_payment_method_script_handles(): array {
		$script_path = EUROLEDGER_XRPL_GATEWAY_DIR . 'assets/js/blocks-checkout.js';
		$script_url  = plugins_url( 'assets/js/blocks-checkout.js', EUROLEDGER_XRPL_GATEWAY_FILE );
		$version     = file_exists( $script_path )
			? (string) filemtime( $script_path )
			: EUROLEDGER_XRPL_GATEWAY_VERSION;

		wp_register_script(
			'euroledger-xrpl-blocks-checkout',
			$script_url,
			array(
				'wc-blocks-registry',
				'wc-settings',
				'wp-element',
				'wp-html-entities',
				'wp-i18n',
			),
			$version,
			true
		);

		return array( 'euroledger-xrpl-blocks-checkout' );
	}

	/**
	 * Return data exposed to the Blocks checkout script.
	 *
	 * @return array<string, mixed>
	 */
	public function get_payment_method_data(): array {
		return array(
			'title'       => $this->get_gateway_setting( 'title', __( 'EuroLedger XRPL', 'euroledger-xrpl-gateway' ) ),
			'description' => $this->get_gateway_setting( 'description', __( 'Pay using a EuroLedger XRPL payment intent.', 'euroledger-xrpl-gateway' ) ),
			'supports'    => array( 'products' ),
		);
	}

	/**
	 * Return a string setting value.
	 *
	 * @param string $key Setting key.
	 * @param string $default Default value.
	 * @return string
	 */
	private function get_gateway_setting( string $key, string $default = '' ): string {
		$value = $this->settings[ $key ] ?? $default;

		return is_scalar( $value ) ? trim( (string) $value ) : $default;
	}

	/**
	 * Return whether checkout can safely offer this payment method.
	 *
	 * @return bool
	 */
	private function has_required_checkout_configuration(): bool {
		$api_base_url     = $this->get_gateway_setting( 'api_base_url', '' );
		$merchant_api_key = $this->get_gateway_setting( 'merchant_api_key', '' );
		$webhook_secret   = $this->get_gateway_setting( 'webhook_secret', '' );

		return '' !== $api_base_url
			&& $this->is_http_url( $api_base_url )
			&& '' !== $merchant_api_key
			&& '' !== $webhook_secret;
	}

	/**
	 * Return whether a URL is HTTP or HTTPS.
	 *
	 * @param string $url URL to inspect.
	 * @return bool
	 */
	private function is_http_url( string $url ): bool {
		$scheme = wp_parse_url( $url, PHP_URL_SCHEME );

		return in_array( $scheme, array( 'http', 'https' ), true );
	}
}

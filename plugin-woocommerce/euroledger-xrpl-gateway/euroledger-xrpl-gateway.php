<?php
/**
 * Plugin Name: EuroLedger XRPL Gateway
 * Plugin URI: https://github.com/pitill0/euroledger-xrpl
 * Description: Experimental WooCommerce payment gateway for EuroLedger XRPL.
 * Version: 0.1.0
 * Author: EuroLedger XRPL
 * License: Apache-2.0
 * Requires at least: 6.4
 * Requires PHP: 8.0
 * WC requires at least: 8.0
 * WC tested up to: 9.0
 * Requires Plugins: woocommerce
 * Text Domain: euroledger-xrpl-gateway
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'EUROLEDGER_XRPL_GATEWAY_VERSION', '0.1.0' );
define( 'EUROLEDGER_XRPL_GATEWAY_FILE', __FILE__ );
define( 'EUROLEDGER_XRPL_GATEWAY_DIR', plugin_dir_path( __FILE__ ) );

/**
 * Register HPOS compatibility.
 */
function euroledger_xrpl_gateway_declare_woocommerce_features(): void {
	if ( ! class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
		return;
	}

	\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
		'custom_order_tables',
		__FILE__,
		true
	);
}
add_action(
	'before_woocommerce_init',
	'euroledger_xrpl_gateway_declare_woocommerce_features'
);

/**
 * Load the gateway class after WooCommerce is available.
 */
function euroledger_xrpl_gateway_init(): void {
	if ( ! class_exists( 'WC_Payment_Gateway' ) ) {
		add_action(
			'admin_notices',
			'euroledger_xrpl_gateway_missing_woocommerce_notice'
		);
		return;
	}

	require_once EUROLEDGER_XRPL_GATEWAY_DIR . 'includes/class-euroledger-xrpl-api-client.php';
	require_once EUROLEDGER_XRPL_GATEWAY_DIR . 'includes/class-euroledger-xrpl-webhook-receiver.php';
	require_once EUROLEDGER_XRPL_GATEWAY_DIR . 'includes/class-euroledger-xrpl-gateway.php';

	$webhook_receiver = new EuroLedger_XRPL_Webhook_Receiver();
	$webhook_receiver->register();
}
add_action( 'plugins_loaded', 'euroledger_xrpl_gateway_init', 11 );

/**
 * Show an admin notice when WooCommerce is not active.
 */
function euroledger_xrpl_gateway_missing_woocommerce_notice(): void {
	if ( ! current_user_can( 'activate_plugins' ) ) {
		return;
	}

	echo '<div class="notice notice-error"><p>';
	echo esc_html__(
		'EuroLedger XRPL Gateway requires WooCommerce to be active.',
		'euroledger-xrpl-gateway'
	);
	echo '</p></div>';
}

/**
 * Register EuroLedger XRPL as a WooCommerce payment gateway.
 *
 * @param array<int|string, string> $gateways Registered gateway classes.
 * @return array<int|string, string>
 */
function euroledger_xrpl_gateway_register( array $gateways ): array {
	$gateways[] = 'WC_Gateway_EuroLedger_XRPL';

	return $gateways;
}
add_filter( 'woocommerce_payment_gateways', 'euroledger_xrpl_gateway_register' );

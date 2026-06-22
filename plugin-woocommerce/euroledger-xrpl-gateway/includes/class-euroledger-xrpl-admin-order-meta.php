<?php
/**
 * EuroLedger XRPL admin order metadata panel.
 *
 * @package EuroLedger_XRPL_Gateway
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Renders EuroLedger XRPL payment metadata on WooCommerce admin order screens.
 */
class EuroLedger_XRPL_Admin_Order_Meta {
	/**
	 * Register WordPress hooks.
	 */
	public function register(): void {
		add_action(
			'woocommerce_admin_order_data_after_order_details',
			array( $this, 'render_order_metadata_panel' )
		);
	}

	/**
	 * Render EuroLedger XRPL metadata on the order edit screen.
	 *
	 * @param WC_Order $order WooCommerce order.
	 */
	public function render_order_metadata_panel( WC_Order $order ): void {
		$fields = $this->get_metadata_fields( $order );

		if ( empty( $fields ) ) {
			return;
		}

		echo '<div class="euroledger-xrpl-admin-order-meta">';
		echo '<h3>' . esc_html__( 'EuroLedger XRPL payment', 'euroledger-xrpl-gateway' ) . '</h3>';
		echo '<table class="widefat striped">';
		echo '<tbody>';

		foreach ( $fields as $label => $value ) {
			echo '<tr>';
			echo '<th scope="row">' . esc_html( $label ) . '</th>';
			echo '<td><code>' . esc_html( $value ) . '</code></td>';
			echo '</tr>';
		}

		echo '</tbody>';
		echo '</table>';
		echo '</div>';
	}

	/**
	 * Build the list of metadata fields to render.
	 *
	 * @param WC_Order $order WooCommerce order.
	 * @return array<string, string>
	 */
	private function get_metadata_fields( WC_Order $order ): array {
		$metadata = array(
			__( 'Payment intent ID', 'euroledger-xrpl-gateway' ) => '_euroledger_payment_intent_id',
			__( 'Payment reference', 'euroledger-xrpl-gateway' ) => '_euroledger_payment_intent_reference',
			__( 'EuroLedger status', 'euroledger-xrpl-gateway' ) => '_euroledger_payment_intent_status',
			__( 'Payment intent created at', 'euroledger-xrpl-gateway' ) => '_euroledger_payment_intent_created_at',
			__( 'Payment intent confirmed at', 'euroledger-xrpl-gateway' ) => '_euroledger_payment_intent_confirmed_at',
			__( 'XRPL transaction hash', 'euroledger-xrpl-gateway' ) => '_euroledger_xrpl_transaction_hash',
			__( 'Last webhook event', 'euroledger-xrpl-gateway' ) => '_euroledger_webhook_last_event',
			__( 'Last webhook delivery ID', 'euroledger-xrpl-gateway' ) => '_euroledger_webhook_last_delivery_id',
			__( 'Last webhook timestamp', 'euroledger-xrpl-gateway' ) => '_euroledger_webhook_last_timestamp',
		);

		$fields = array();

		foreach ( $metadata as $label => $meta_key ) {
			$value = trim( (string) $order->get_meta( $meta_key ) );

			if ( '' === $value ) {
				continue;
			}

			$fields[ $label ] = $value;
		}

		return $fields;
	}
}

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
	private const OPTION_NAME = 'woocommerce_euroledger_xrpl_settings';

	/**
	 * Register WordPress hooks.
	 */
	public function register(): void {
		add_action( 'add_meta_boxes', array( $this, 'register_order_meta_box' ) );

		add_filter( 'manage_edit-shop_order_columns', array( $this, 'add_orders_list_column' ) );
		add_action( 'manage_shop_order_posts_custom_column', array( $this, 'render_legacy_orders_list_column' ), 10, 2 );

		add_filter( 'manage_woocommerce_page_wc-orders_columns', array( $this, 'add_orders_list_column' ) );
		add_action( 'manage_woocommerce_page_wc-orders_custom_column', array( $this, 'render_hpos_orders_list_column' ), 10, 2 );
	}

	/**
	 * Register a dedicated full-width WooCommerce order meta box.
	 */
	public function register_order_meta_box(): void {
		$screens = array( 'shop_order' );

		if ( function_exists( 'wc_get_page_screen_id' ) ) {
			$screens[] = wc_get_page_screen_id( 'shop-order' );
		}

		foreach ( array_unique( $screens ) as $screen ) {
			add_meta_box(
				'euroledger-xrpl-payment',
				__( 'EuroLedger XRPL payment', 'euroledger-xrpl-gateway' ),
				array( $this, 'render_order_metadata_meta_box' ),
				$screen,
				'normal',
				'high'
			);
		}
	}


	/**
	 * Add a compact EuroLedger column to WooCommerce order lists.
	 *
	 * @param array<string, string> $columns Existing order list columns.
	 * @return array<string, string>
	 */
	public function add_orders_list_column( array $columns ): array {
		$new_columns = array();
		$inserted    = false;

		foreach ( $columns as $key => $label ) {
			$new_columns[ $key ] = $label;

			if ( 'order_status' === $key ) {
				$new_columns['euroledger_xrpl'] = __( 'EuroLedger', 'euroledger-xrpl-gateway' );
				$inserted = true;
			}
		}

		if ( ! $inserted ) {
			$new_columns['euroledger_xrpl'] = __( 'EuroLedger', 'euroledger-xrpl-gateway' );
		}

		return $new_columns;
	}

	/**
	 * Render the legacy posts-table EuroLedger order column.
	 *
	 * @param string $column  Column key.
	 * @param int    $post_id Order post id.
	 */
	public function render_legacy_orders_list_column( string $column, int $post_id ): void {
		if ( 'euroledger_xrpl' !== $column ) {
			return;
		}

		$order = wc_get_order( $post_id );
		$this->render_orders_list_column( $order );
	}

	/**
	 * Render the HPOS WooCommerce orders-table EuroLedger order column.
	 *
	 * @param string        $column Column key.
	 * @param WC_Order|int $order  WooCommerce order object or id.
	 */
	public function render_hpos_orders_list_column( string $column, $order ): void {
		if ( 'euroledger_xrpl' !== $column ) {
			return;
		}

		if ( ! $order instanceof WC_Order ) {
			$order = wc_get_order( $order );
		}

		$this->render_orders_list_column( $order );
	}

	/**
	 * Render the metadata panel inside the order meta box.
	 *
	 * @param WP_Post|WC_Order $post_or_order_object Current order screen object.
	 */
	public function render_order_metadata_meta_box( $post_or_order_object ): void {
		$order = null;

		if ( $post_or_order_object instanceof WC_Order ) {
			$order = $post_or_order_object;
		} elseif ( $post_or_order_object instanceof WP_Post ) {
			$order = wc_get_order( $post_or_order_object->ID );
		}

		if ( ! $order instanceof WC_Order ) {
			echo '<p>' . esc_html__( 'Unable to load EuroLedger payment metadata for this order.', 'euroledger-xrpl-gateway' ) . '</p>';
			return;
		}

		$this->render_order_metadata_panel( $order );
	}

	/**
	 * Render EuroLedger XRPL metadata on the order edit screen.
	 *
	 * @param WC_Order $order WooCommerce order.
	 */
	public function render_order_metadata_panel( WC_Order $order ): void {
		$payment_intent_id = trim( (string) $order->get_meta( '_euroledger_payment_intent_id' ) );

		if ( '' === $payment_intent_id ) {
			return;
		}

		$fields        = $this->get_metadata_fields( $order );
		$status        = trim( (string) $order->get_meta( '_euroledger_payment_intent_status' ) );
		$reference     = trim( (string) $order->get_meta( '_euroledger_payment_intent_reference' ) );
		$dashboard_url = $this->build_dashboard_payment_intent_url( $payment_intent_id );

		$this->render_inline_assets();

		echo '<section class="euroledger-xrpl-admin-card" aria-label="' . esc_attr__( 'EuroLedger XRPL payment metadata', 'euroledger-xrpl-gateway' ) . '">';
		echo '<div class="euroledger-xrpl-admin-card__header">';
		echo '<div>';
		echo '<h3>' . esc_html__( 'EuroLedger XRPL payment', 'euroledger-xrpl-gateway' ) . '</h3>';
		echo '<p>' . esc_html__( 'Signed backend payment intent linked to this WooCommerce order.', 'euroledger-xrpl-gateway' ) . '</p>';
		echo '</div>';
		echo $this->render_status_badge( $status );
		echo '</div>';

		echo '<div class="euroledger-xrpl-admin-card__summary">';
		$this->render_summary_item(
			__( 'Reference', 'euroledger-xrpl-gateway' ),
			$reference,
			true
		);
		$this->render_summary_item(
			__( 'Payment intent', 'euroledger-xrpl-gateway' ),
			$payment_intent_id,
			true
		);
		echo '</div>';

		if ( '' !== $dashboard_url ) {
			echo '<p class="euroledger-xrpl-admin-card__actions">';
			echo '<a class="button button-secondary" href="' . esc_url( $dashboard_url ) . '" target="_blank" rel="noopener noreferrer">';
			echo esc_html__( 'View in EuroLedger', 'euroledger-xrpl-gateway' );
			echo '</a>';
			echo '</p>';
		}

		echo '<dl class="euroledger-xrpl-admin-card__details">';
		foreach ( $fields as $field ) {
			$this->render_detail_row( $field['label'], $field['value'], $field['copyable'] );
		}
		echo '</dl>';
		echo '</section>';
	}


	/**
	 * Render one compact EuroLedger cell in the WooCommerce orders list.
	 *
	 * @param WC_Order|false $order WooCommerce order.
	 */
	private function render_orders_list_column( $order ): void {
		if ( ! $order instanceof WC_Order ) {
			echo '<span aria-hidden="true">&mdash;</span>';
			return;
		}

		$payment_intent_id = trim( (string) $order->get_meta( '_euroledger_payment_intent_id' ) );

		if ( '' === $payment_intent_id ) {
			echo '<span aria-hidden="true">&mdash;</span>';
			return;
		}

		$status        = trim( (string) $order->get_meta( '_euroledger_payment_intent_status' ) );
		$reference     = trim( (string) $order->get_meta( '_euroledger_payment_intent_reference' ) );
		$dashboard_url = $this->build_dashboard_payment_intent_url( $payment_intent_id );

		$this->render_orders_list_assets();

		echo '<div class="euroledger-xrpl-orders-list-cell">';
		echo $this->render_orders_list_status_badge( $status );

		if ( '' !== $reference ) {
			echo '<code class="euroledger-xrpl-orders-list-cell__reference">' . esc_html( $reference ) . '</code>';
		}

		if ( '' !== $dashboard_url ) {
			echo '<a class="euroledger-xrpl-orders-list-cell__link" href="' . esc_url( $dashboard_url ) . '" target="_blank" rel="noopener noreferrer">';
			echo esc_html__( 'View', 'euroledger-xrpl-gateway' );
			echo '</a>';
		}

		echo '</div>';
	}

	/**
	 * Render inline CSS needed by the compact orders list column.
	 */
	private function render_orders_list_assets(): void {
		static $rendered = false;

		if ( $rendered ) {
			return;
		}

		$rendered = true;
		?>
		<style>
			.column-euroledger_xrpl { width: 150px; }
			.euroledger-xrpl-orders-list-cell {
				align-items: flex-start;
				display: flex;
				flex-direction: column;
				gap: 5px;
			}
			.euroledger-xrpl-orders-list-cell__badge {
				border-radius: 999px;
				display: inline-flex;
				font-size: 11px;
				font-weight: 600;
				line-height: 1;
				padding: 5px 8px;
				text-transform: uppercase;
				white-space: nowrap;
			}
			.euroledger-xrpl-orders-list-cell__badge--confirmed { background: #d1e7dd; color: #0f5132; }
			.euroledger-xrpl-orders-list-cell__badge--pending { background: #fff3cd; color: #664d03; }
			.euroledger-xrpl-orders-list-cell__badge--expired,
			.euroledger-xrpl-orders-list-cell__badge--cancelled { background: #f8d7da; color: #842029; }
			.euroledger-xrpl-orders-list-cell__badge--unknown { background: #e2e3e5; color: #41464b; }
			.euroledger-xrpl-orders-list-cell__reference {
				background: #f6f7f7;
				border-radius: 4px;
				font-size: 11px;
				max-width: 100%;
				overflow-wrap: anywhere;
				padding: 2px 5px;
			}
			.euroledger-xrpl-orders-list-cell__link {
				font-size: 12px;
			}
		</style>
		<?php
	}

	/**
	 * Render the small inline CSS and JS needed by the admin card.
	 */
	private function render_inline_assets(): void {
		static $rendered = false;

		if ( $rendered ) {
			return;
		}

		$rendered = true;
		?>
		<style>
			.euroledger-xrpl-admin-card {
				background: #fff;
				clear: both;
				margin: -6px -12px -12px;
				overflow: hidden;
			}
			.euroledger-xrpl-admin-card__header {
				align-items: flex-start;
				background: #f6f7f7;
				display: flex;
				gap: 16px;
				justify-content: space-between;
				padding: 16px 18px;
			}
			.euroledger-xrpl-admin-card__header h3 {
				font-size: 15px;
				line-height: 1.3;
				margin: 0 0 4px;
			}
			.euroledger-xrpl-admin-card__header p {
				color: #646970;
				margin: 0;
			}
			.euroledger-xrpl-admin-card__badge {
				border-radius: 999px;
				display: inline-flex;
				font-size: 12px;
				font-weight: 600;
				line-height: 1;
				padding: 7px 10px;
				text-transform: uppercase;
				white-space: nowrap;
			}
			.euroledger-xrpl-admin-card__badge--confirmed { background: #d1e7dd; color: #0f5132; }
			.euroledger-xrpl-admin-card__badge--pending { background: #fff3cd; color: #664d03; }
			.euroledger-xrpl-admin-card__badge--expired,
			.euroledger-xrpl-admin-card__badge--cancelled { background: #f8d7da; color: #842029; }
			.euroledger-xrpl-admin-card__badge--unknown { background: #e2e3e5; color: #41464b; }
			.euroledger-xrpl-admin-card__summary {
				display: grid;
				gap: 14px;
				grid-template-columns: minmax(220px, .7fr) minmax(360px, 1.3fr);
				padding: 16px 18px 4px;
			}
			.euroledger-xrpl-admin-card__summary-item,
			.euroledger-xrpl-admin-card__details > div {
				min-width: 0;
			}
			.euroledger-xrpl-admin-card__label,
			.euroledger-xrpl-admin-card__details dt {
				color: #646970;
				font-size: 12px;
				font-weight: 600;
				letter-spacing: .02em;
				margin: 0 0 5px;
				text-transform: uppercase;
			}
			.euroledger-xrpl-admin-card__value,
			.euroledger-xrpl-admin-card__details dd code {
				background: #f6f7f7;
				border-radius: 4px;
				display: inline-block;
				font-size: 12px;
				max-width: 100%;
				padding: 4px 6px;
				white-space: normal;
				word-break: break-all;
			}
			.euroledger-xrpl-admin-card__details {
				border-top: 1px solid #dcdcde;
				display: grid;
				grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
				margin: 16px 0 0;
			}
			.euroledger-xrpl-admin-card__details dt,
			.euroledger-xrpl-admin-card__details dd {
				border-bottom: 1px solid #f0f0f1;
				margin: 0;
				padding: 12px 18px;
			}
			.euroledger-xrpl-admin-card__details dd {
				align-items: center;
				display: flex;
				gap: 8px;
				justify-content: space-between;
			}
			.euroledger-xrpl-admin-card__actions {
				margin: 12px 18px 0;
			}
			.euroledger-xrpl-admin-card__copy {
				flex: 0 0 auto;
			}
			@media (max-width: 960px) {
				.euroledger-xrpl-admin-card__summary {
					grid-template-columns: 1fr;
				}
			}
			@media (max-width: 782px) {
				.euroledger-xrpl-admin-card__header,
				.euroledger-xrpl-admin-card__details dd {
					align-items: flex-start;
					flex-direction: column;
				}
				.euroledger-xrpl-admin-card__details {
					grid-template-columns: 1fr;
				}
				.euroledger-xrpl-admin-card__details dt {
					border-bottom: 0;
					padding-bottom: 0;
				}
			}
		</style>
		<script>
			document.addEventListener('click', function (event) {
				var button = event.target.closest('.euroledger-xrpl-admin-card__copy');

				if (!button) {
					return;
				}

				var value = button.getAttribute('data-copy-value') || '';
				var originalText = button.textContent;

				if (!value) {
					return;
				}

				function markCopied() {
					button.textContent = button.getAttribute('data-copied-label') || 'Copied';
					window.setTimeout(function () {
						button.textContent = originalText;
					}, 1400);
				}

				if (navigator.clipboard && window.isSecureContext) {
					navigator.clipboard.writeText(value).then(markCopied);
					return;
				}

				var textarea = document.createElement('textarea');
				textarea.value = value;
				textarea.setAttribute('readonly', 'readonly');
				textarea.style.position = 'absolute';
				textarea.style.left = '-9999px';
				document.body.appendChild(textarea);
				textarea.select();

				try {
					document.execCommand('copy');
					markCopied();
				} finally {
					document.body.removeChild(textarea);
				}
			});
		</script>
		<?php
	}

	/**
	 * Render a summary item.
	 *
	 * @param string $label Field label.
	 * @param string $value Field value.
	 * @param bool   $copyable Whether to show a copy button.
	 */
	private function render_summary_item( string $label, string $value, bool $copyable ): void {
		if ( '' === $value ) {
			return;
		}

		echo '<div class="euroledger-xrpl-admin-card__summary-item">';
		echo '<p class="euroledger-xrpl-admin-card__label">' . esc_html( $label ) . '</p>';
		echo '<code class="euroledger-xrpl-admin-card__value">' . esc_html( $value ) . '</code>';
		if ( $copyable ) {
			$this->render_copy_button( $value );
		}
		echo '</div>';
	}

	/**
	 * Render one detail row.
	 *
	 * @param string $label Field label.
	 * @param string $value Field value.
	 * @param bool   $copyable Whether to show a copy button.
	 */
	private function render_detail_row( string $label, string $value, bool $copyable ): void {
		echo '<dt>' . esc_html( $label ) . '</dt>';
		echo '<dd>';
		echo '<code>' . esc_html( $value ) . '</code>';
		if ( $copyable ) {
			$this->render_copy_button( $value );
		}
		echo '</dd>';
	}

	/**
	 * Render a copy-to-clipboard button.
	 *
	 * @param string $value Value to copy.
	 */
	private function render_copy_button( string $value ): void {
		echo '<button type="button" class="button button-small euroledger-xrpl-admin-card__copy" data-copy-value="' . esc_attr( $value ) . '" data-copied-label="' . esc_attr__( 'Copied', 'euroledger-xrpl-gateway' ) . '">';
		echo esc_html__( 'Copy', 'euroledger-xrpl-gateway' );
		echo '</button>';
	}


	/**
	 * Render the compact payment status badge used in WooCommerce orders list.
	 *
	 * @param string $status Payment intent status.
	 * @return string
	 */
	private function render_orders_list_status_badge( string $status ): string {
		$normalized_status = sanitize_html_class( strtolower( trim( $status ) ) );
		$known_statuses    = array( 'pending', 'confirmed', 'expired', 'cancelled' );

		if ( '' === $normalized_status || ! in_array( $normalized_status, $known_statuses, true ) ) {
			$normalized_status = 'unknown';
		}

		$label = '' === $status ? __( 'Unknown', 'euroledger-xrpl-gateway' ) : $status;

		return sprintf(
			'<span class="euroledger-xrpl-orders-list-cell__badge euroledger-xrpl-orders-list-cell__badge--%1$s">%2$s</span>',
			esc_attr( $normalized_status ),
			esc_html( $label )
		);
	}

	/**
	 * Render the payment status badge.
	 *
	 * @param string $status Payment intent status.
	 * @return string
	 */
	private function render_status_badge( string $status ): string {
		$normalized_status = sanitize_html_class( strtolower( trim( $status ) ) );
		$known_statuses    = array( 'pending', 'confirmed', 'expired', 'cancelled' );

		if ( '' === $normalized_status || ! in_array( $normalized_status, $known_statuses, true ) ) {
			$normalized_status = 'unknown';
		}

		$label = '' === $status ? __( 'Unknown', 'euroledger-xrpl-gateway' ) : $status;

		return sprintf(
			'<span class="euroledger-xrpl-admin-card__badge euroledger-xrpl-admin-card__badge--%1$s">%2$s</span>',
			esc_attr( $normalized_status ),
			esc_html( $label )
		);
	}

	/**
	 * Build the list of metadata fields to render.
	 *
	 * @param WC_Order $order WooCommerce order.
	 * @return array<int, array{label: string, value: string, copyable: bool}>
	 */
	private function get_metadata_fields( WC_Order $order ): array {
		$metadata = array(
			array(
				'label'    => __( 'EuroLedger status', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_status',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Payment intent created at', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_created_at',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Payment intent confirmed at', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_confirmed_at',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Payment intent expires at', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_expires_at',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Payment intent cancelled at', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_cancelled_at',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Cancellation reason', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_payment_intent_cancellation_reason',
				'copyable' => false,
			),
			array(
				'label'    => __( 'XRPL transaction hash', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_xrpl_transaction_hash',
				'copyable' => true,
			),
			array(
				'label'    => __( 'Last webhook event', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_webhook_last_event',
				'copyable' => false,
			),
			array(
				'label'    => __( 'Last webhook delivery ID', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_webhook_last_delivery_id',
				'copyable' => true,
			),
			array(
				'label'    => __( 'Last webhook timestamp', 'euroledger-xrpl-gateway' ),
				'meta_key' => '_euroledger_webhook_last_timestamp',
				'copyable' => false,
			),
		);

		$fields = array();

		foreach ( $metadata as $field ) {
			$value = trim( (string) $order->get_meta( $field['meta_key'] ) );

			if ( '' === $value ) {
				continue;
			}

			$fields[] = array(
				'label'    => $field['label'],
				'value'    => $value,
				'copyable' => $field['copyable'],
			);
		}

		return $fields;
	}

	/**
	 * Build a dashboard URL for a payment intent when configured.
	 *
	 * @param string $payment_intent_id Payment intent id.
	 * @return string
	 */
	private function build_dashboard_payment_intent_url( string $payment_intent_id ): string {
		$base_url = $this->get_dashboard_base_url();

		if ( '' === $base_url || '' === $payment_intent_id ) {
			return '';
		}

		$fragment = '';
		$base_without_fragment = $base_url;

		if ( false !== strpos( $base_without_fragment, '#' ) ) {
			list( $base_without_fragment, $fragment ) = explode( '#', $base_without_fragment, 2 );
		}

		$query = '';
		$base_without_query = $base_without_fragment;

		if ( false !== strpos( $base_without_query, '?' ) ) {
			list( $base_without_query, $query ) = explode( '?', $base_without_query, 2 );
		}

		$payment_intent_url = trailingslashit( $base_without_query ) . 'payment-intents/' . rawurlencode( $payment_intent_id );

		if ( '' !== $query ) {
			$payment_intent_url .= '?' . $query;
		}

		if ( '' !== $fragment ) {
			$payment_intent_url .= '#' . $fragment;
		}

		return $payment_intent_url;
	}

	/**
	 * Get the configured dashboard base URL.
	 *
	 * @return string
	 */
	private function get_dashboard_base_url(): string {
		$settings = get_option( self::OPTION_NAME, array() );

		if ( ! is_array( $settings ) ) {
			return '';
		}

		return untrailingslashit( trim( (string) ( $settings['dashboard_base_url'] ?? '' ) ) );
	}
}

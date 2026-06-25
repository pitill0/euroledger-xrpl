(function () {
	const { registerPaymentMethod } = window.wc.wcBlocksRegistry;
	const { getSetting } = window.wc.wcSettings;
	const { createElement } = window.wp.element;
	const { decodeEntities } = window.wp.htmlEntities;
	const { __ } = window.wp.i18n;

	const settings = getSetting('euroledger_xrpl_data', {});
	const title = decodeEntities(settings.title || __('EuroLedger XRPL', 'euroledger-xrpl-gateway'));
	const description = decodeEntities(
		settings.description ||
			__('Pay using a EuroLedger XRPL payment intent.', 'euroledger-xrpl-gateway')
	);
	const supports = settings.supports || ['products'];

	const Label = () => createElement('span', null, title);

	const Content = () =>
		createElement(
			'div',
			{ className: 'euroledger-xrpl-blocks-checkout' },
			createElement('p', null, description)
		);

	registerPaymentMethod({
		name: 'euroledger_xrpl',
		label: createElement(Label, null),
		content: createElement(Content, null),
		edit: createElement(Content, null),
		canMakePayment: () => true,
		ariaLabel: title,
		supports: {
			features: supports,
		},
	});
})();

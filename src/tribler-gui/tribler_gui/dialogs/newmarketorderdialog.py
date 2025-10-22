from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QSizePolicy

from tribler_gui.dialogs.dialogcontainer import DialogContainer
from tribler_gui.utilities import get_ui_file_path


class NewMarketOrderDialog(DialogContainer):

    button_clicked = pyqtSignal(int)

    def __init__(self, parent, is_ask, asset1_type, asset2_type, wallets):
        DialogContainer.__init__(self, parent)

        self.is_ask = is_ask
        self.price = 0.0
        self.price_type = asset2_type
        self.quantity = -1
        self.quantity_type = asset1_type
        self.wallets = wallets

        # These asset amount values are only set when the order has been verified on the GUI side
        self.asset1_amount = 0
        self.asset2_amount = 0

        uic.loadUi(get_ui_file_path('newmarketorderdialog.ui'), self.dialog_widget)

        self.dialog_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.dialog_widget.error_text_label.hide()

        if is_ask:
            self.dialog_widget.new_order_title_label.setText('Sell %s for %s' % (asset1_type, asset2_type))
        else:
            self.dialog_widget.new_order_title_label.setText('Buy %s for %s' % (asset1_type, asset2_type))

        self.dialog_widget.quantity_label.setText("Volume (%s):" % asset1_type)
        self.dialog_widget.price_label.setText("Price per unit (%s / %s):" % (asset2_type, asset1_type))

        self.dialog_widget.create_button.clicked.connect(self.on_create_clicked)
        self.dialog_widget.cancel_button.clicked.connect(lambda: self.button_clicked.emit(0))

        self.update_window()

    def on_create_clicked(self):
        # Validate user input
        try:
            self.quantity = float(self.dialog_widget.order_quantity_input.text())
        except ValueError:
            self.dialog_widget.error_text_label.setText("The quantity must be a valid number.")
            self.dialog_widget.error_text_label.show()
            return

        try:
            self.price = float(self.dialog_widget.order_price_input.text())
        except ValueError:
            self.dialog_widget.error_text_label.setText("The price must be a valid number.")
            self.dialog_widget.error_text_label.show()
            return

        # Check whether we are trading at least the minimum amount of assets
        asset1_amount = int(self.quantity * (10 ** self.wallets[self.quantity_type]["precision"]))
        if asset1_amount < self.wallets[self.quantity_type]['min_unit']:
            min_amount = float(self.wallets[self.quantity_type]["min_unit"]) / float(
                10 ** self.wallets[self.quantity_type]["precision"]
            )
            self.dialog_widget.error_text_label.setText(
                "The quantity is less than the minimum amount (%g %s)." % (min_amount, self.quantity_type)
            )
            self.dialog_widget.error_text_label.show()
            return

        price_num = self.price * (10 ** self.wallets[self.price_type]["precision"])
        price_denom = float(10 ** self.wallets[self.quantity_type]["precision"])
        price = price_num / price_denom
        asset2_amount = int(asset1_amount * price)

        # Check whether the price will lead to a trade where at least the minimum amount of assets are exchanged
        if asset2_amount < self.wallets[self.price_type]['min_unit']:
            min_amount = float(self.wallets[self.price_type]["min_unit"]) / float(
                10 ** self.wallets[self.price_type]["precision"]
            )
            self.dialog_widget.error_text_label.setText(
                "The price leads to a trade where less than the minimum amount "
                "of assets are exchanged (%g %s)." % (min_amount, self.price_type)
            )
            self.dialog_widget.error_text_label.show()
            return

        # Everything is valid, proceed with order creation
        self.asset1_amount = asset1_amount
        self.asset2_amount = asset2_amount
        self.update_window()
        self.button_clicked.emit(1)

    def update_window(self):
        self.dialog_widget.adjustSize()
        self.on_main_window_resize()

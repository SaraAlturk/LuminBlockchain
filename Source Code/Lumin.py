import json
import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QTabWidget, QWidget,
                             QTableWidget, QTableWidgetItem, QDoubleSpinBox, QLabel, QPushButton,
                             QFormLayout, QStatusBar, QListWidget, QLineEdit, QDialog, QProgressBar,
                             QHBoxLayout, QComboBox, QInputDialog, QMessageBox, QListWidgetItem)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from web3 import Web3

# Setup logging
logging.basicConfig(filename='application.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to local Ethereum node via ganache's cli
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Path to the ABI file generated by Truffle, modify as needed
abi_file_path = "build/contracts/EnergyManagement.json"

# Load the ABI
try:
    with open(abi_file_path, 'r') as abi_file:
        abi = json.load(abi_file)['abi']
except FileNotFoundError:
    logging.error(f"ABI file not found at {abi_file_path}")
    sys.exit(f"Error: ABI file not found at {abi_file_path}")
except json.JSONDecodeError:
    logging.error(f"Error decoding ABI JSON from {abi_file_path}")
    sys.exit("Error: ABI file is not a valid JSON")

# Contract details
contract_address = '0xyoucontractaddress'

# Create the contract instance
try:
    contract = web3.eth.contract(address=contract_address, abi=abi)
except Exception as e:
    logging.error(f"Failed to create contract instance: {e}")
    sys.exit("Error: Failed to create contract instance")


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 450)

        layout = QVBoxLayout()

        # Set the desired font style and size
        font = QFont("Arial", 11)

        # Add the motto
        motto_label = QLabel("Welcome to Lumin, a Blockchain-Based Solar Energy Management System", self)
        motto_label.setFont(font)
        motto_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(motto_label)

        # Add the minimized logo
        logo_label = QLabel(self)
        try:
            # Enter the path where the logo is saved
            pixmap = QPixmap("Lumin.png").scaled(500, 290)
            logo_label.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Failed to load logo image: {e}")
            logo_label.setText("Logo not available")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Add the role dropdown
        self.role_combo = QComboBox(self)
        self.role_combo.setFont(font)
        self.role_combo.addItem("Select Role")
        self.role_combo.addItem("Manager")
        self.role_combo.addItem("User")
        layout.addWidget(self.role_combo)

        # Add the username and password fields
        self.username_field = QLineEdit(self)
        self.username_field.setPlaceholderText("Username")
        self.username_field.setFont(font)
        layout.addWidget(self.username_field)

        self.password_field = QLineEdit(self)
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText("Password")
        self.password_field.setFont(font)
        layout.addWidget(self.password_field)

        # Add the login button
        login_button = QPushButton("LOGIN", self)
        login_button.setFont(font)
        login_button.setStyleSheet("background-color: #224156; color: white; font-weight: bold;")
        login_button.clicked.connect(self.check_login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def check_login(self):
        username = self.username_field.text()
        password = self.password_field.text()
        role = self.role_combo.currentText()

        if role == "Select Role":
            QMessageBox.warning(self, "Role Selection", "Please select a role before logging in.")
            return

        # Hash the password using keccak256
        password_hash = web3.keccak(text=password)

        try:
            accounts = web3.eth.accounts
            for address in accounts:
                user = contract.functions.users(address).call()

                if user[0] == username and user[2] == password_hash:
                    if (role == "Manager" and user[4]) or (role == "User" and not user[4]):
                        self.accept()
                        self.manager = user[4]
                        self.user_address = address  # Store the logged-in user's address
                        return
                    else:
                        QMessageBox.warning(self, "Login Failed", "Selected role does not match the user's role.")
                        self.username_field.clear()
                        self.password_field.clear()
                        self.role_combo.setCurrentIndex(0)
                        return
            QMessageBox.warning(self, "Login Failed", "Invalid username or password. Please try again.")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            QMessageBox.critical(self, "Login Error", "An unexpected error occurred during login.")
            sys.exit("Error: Login failed")


class SolarEnergySystem(QMainWindow):
    def __init__(self, user_address, is_manager=False):
        super().__init__()

        self.user_address = user_address  # Store the logged-in user's address
        self.is_manager = is_manager
        self.setWindowTitle("Solar Energy Trading System")
        self.setGeometry(100, 100, 800, 600)

        self.main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        if self.is_manager:
            self.create_manager_tab()
        else:
            self.create_dashboard_and_user_info_tab()
            self.create_buy_and_sell_tab()
            self.create_history_tab()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Add a logout button
        self.logout_button = QPushButton("Logout")
        font = QFont("Arial", 11)
        self.logout_button.setFont(font)
        self.logout_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.logout_button.clicked.connect(self.logout)
        self.status_bar.addPermanentWidget(self.logout_button)

    def logout(self):
        self.close()  # Close the current window
        self.login_window = LoginWindow()  # Create a new instance of the login window
        if self.login_window.exec_() == QDialog.Accepted:
            user_address = self.login_window.user_address  # Retrieve the logged-in user's address from the login window
            is_manager = self.login_window.manager
            self.__init__(user_address=user_address, is_manager=is_manager)  # Re-initialize the main window with new user
            self.show()  # Show the main window again

    def create_manager_tab(self):
        manager_tab = QWidget()
        layout = QVBoxLayout()

        # Set the font for headers
        font = QFont("Arial", 11, QFont.Bold)

        # Label for transactions
        transaction_label = QLabel("Transactions")
        transaction_label.setFont(font)
        layout.addWidget(transaction_label)

        self.transaction_list = QListWidget()
        layout.addWidget(self.transaction_list)

        self.transaction_search_field = QLineEdit()
        self.transaction_search_field.setFont(font)
        self.transaction_search_field.setPlaceholderText("Search Transaction by Index")
        self.transaction_search_field.returnPressed.connect(self.search_transaction)
        layout.addWidget(self.transaction_search_field)

        # Label for panels
        panel_label = QLabel("Panels")
        panel_label.setFont(font)
        layout.addWidget(panel_label)

        self.panel_list = QListWidget()
        layout.addWidget(self.panel_list)

        self.panel_search_field = QLineEdit()
        self.panel_search_field.setFont(font)
        self.panel_search_field.setPlaceholderText("Search Panel by ID")
        self.panel_search_field.returnPressed.connect(self.search_panel)
        layout.addWidget(self.panel_search_field)

        # Immediately refresh the data when the manager tab is created
        self.refresh_manager_data()

        manager_tab.setLayout(layout)
        self.tabs.addTab(manager_tab, "Manager Dashboard")

    def refresh_manager_data(self):
        self.panel_list.clear()
        self.transaction_list.clear()

        try:
            panels = contract.functions.displayManagedPanels().call({'from': self.user_address})
            for panel in panels:
                item_text = (
                    f"Panel ID: {panel[0]}, Capacity: {panel[1]} kWh, Location: {panel[2]}, "
                    f"Energy Balance: {panel[5]} kWh, Efficiency: {panel[6]}%"
                )
                item = QListWidgetItem(item_text)
                font = QFont("Arial", 11)  # Set the font size to 11 points
                item.setFont(font)
                self.panel_list.addItem(item)

            transactions = contract.functions.displayManagedTransactions().call({'from': self.user_address})
            for i, tx in enumerate(transactions):
                item_text = (
                    f"Transaction ID: {i}, From: {tx[0]}, To: {tx[1]}, Produced: {tx[2]} kWh, Consumed: {tx[3]} kWh, "
                    f"Tokens: {web3.from_wei(tx[4], 'ether')}, Timestamp: {tx[5]}"
                )
                item = QListWidgetItem(item_text)
                font = QFont("Arial", 11)  # Set the font size to 11 points
                item.setFont(font)
                self.transaction_list.addItem(item)
        except Exception as e:
            logging.error(f"Error refreshing manager data: {e}")
            self.panel_list.addItem("Failed to load panels")
            self.transaction_list.addItem("Failed to load transactions")

    def search_panel(self):
        panel_id = self.panel_search_field.text().strip()
        self.panel_list.clear()

        try:
            panels = contract.functions.displayManagedPanels().call({'from': self.user_address})
            found = False
            for panel in panels:
                if str(panel[0]) == panel_id:
                    item_text = (
                        f"Panel ID: {panel[0]}, Capacity: {panel[1]} kWh, Location: {panel[2]}, "
                        f"Energy Balance: {panel[5]} kWh, Efficiency: {panel[6]}%"
                    )
                    item = QListWidgetItem(item_text)
                    font = QFont("Arial", 11)  # Set the font size to 11 points
                    item.setFont(font)
                    self.panel_list.addItem(item)
                    found = True
                    break

            if not found:
                self.panel_list.addItem("Panel not found")
        except Exception as e:
            logging.error(f"Error searching for panel: {e}")
            self.panel_list.addItem("Failed to search panel")

    def search_transaction(self):
        transaction_index = self.transaction_search_field.text().strip()
        self.transaction_list.clear()

        try:
            transactions = contract.functions.displayManagedTransactions().call({'from': self.user_address})
            if transaction_index.isdigit():
                index = int(transaction_index)
                if 0 <= index < len(transactions):
                    tx = transactions[index]
                    item_text = (
                        f"Transaction ID: {index}, From: {tx[0]}, To: {tx[1]}, Produced: {tx[2]} kWh, Consumed: {tx[3]} kWh, "
                        f"Tokens: {web3.from_wei(tx[4], 'ether')}, Timestamp: {tx[5]}"
                    )
                    item = QListWidgetItem(item_text)
                    font = QFont("Arial", 11)  # Set the font size to 11 points
                    item.setFont(font)
                    self.transaction_list.addItem(item)
                else:
                    self.transaction_list.addItem("Transaction not found")
            else:
                self.transaction_list.addItem("Invalid transaction index")
        except Exception as e:
            logging.error(f"Error searching for transaction: {e}")
            self.transaction_list.addItem("Failed to search transaction")

    def create_dashboard_and_user_info_tab(self):
        dashboard_tab = QWidget()
        main_layout = QVBoxLayout()  # Main layout for the dashboard

        # User Information Form Layout
        user_info_form_layout = QFormLayout()

        try:
            # Set font size
            font = QFont("Arial", 11)

            # Fetch user details from the contract
            user = contract.functions.users(self.user_address).call()

            # Display user's name
            self.name_label = QLabel(user[1] if user[1] else "N/A")  # user[1] is actualName
            self.name_label.setFont(font)  # Set font
            user_info_form_layout.addRow("Name", self.name_label)

            user_info_form_layout.setVerticalSpacing(5)
            self.balance_label = QLabel(f"{web3.from_wei(web3.eth.get_balance(self.user_address), 'ether')} ETH")
            self.balance_label.setFont(font)  # Set font
            user_info_form_layout.addRow("Balance", self.balance_label)

            user_info_form_layout.setVerticalSpacing(15)

            # Panels and Energy Balance Retrieval
            self.panel_info_label = QLabel()
            self.panel_info_label.setFont(font)  # Set font
            self.energy_level_bar = QProgressBar()

            # Create the dropdown for panels below the balance
            self.panel_dropdown = QComboBox()
            self.panel_dropdown.setFont(font)  # Set font
            self.panel_dropdown.setFixedWidth(200)
            user_info_form_layout.addRow("Select Panel", self.panel_dropdown)

            # Refresh panel info to include capacity and energy balance
            self.refresh_panel_info()

            # Add the "Panel Info" label
            user_info_form_layout.addRow("Panel Info", self.panel_info_label)

            # Add the energy level bar below the panel info
            user_info_form_layout.addRow("Energy Level", self.energy_level_bar)

            # Panel Status Label (to be updated based on efficiency)
            self.panel_status_label = QLabel("Panel Status: N/A")
            self.panel_status_label.setFont(font)  # Set font
            self.panel_status_label.setAlignment(Qt.AlignCenter)
            self.panel_status_label.setStyleSheet("padding: 5px; border-radius: 5px;")  # Initial style
            user_info_form_layout.addRow("Panel Status", self.panel_status_label)

            # Handle panel selection changes
            self.panel_dropdown.currentIndexChanged.connect(self.display_selected_panel_info)

            # Display info for the default/first panel when loaded
            if self.panel_dropdown.count() > 0:
                self.display_selected_panel_info()

        except Exception as e:
            logging.error(f"Error fetching user information: {e}")
            self.name_label = QLabel("N/A")
            self.name_label.setFont(font)  # Set font for the error label
            self.panel_info_label = QLabel("N/A")
            self.panel_info_label.setFont(font)  # Set font for the error label

        # Set spacing and margins
        user_info_form_layout.setVerticalSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Add the form layout to the main layout
        main_layout.addLayout(user_info_form_layout)

        # Add the image below the user info section and resize it
        dashboard_image_label = QLabel()
        try:
            # Enter the path where the solar image is saved
            pixmap = QPixmap("Solar.jpg").scaled(1000, 400, Qt.KeepAspectRatio)
            dashboard_image_label.setPixmap(pixmap)
        except Exception as e:
            logging.error(f"Failed to load dashboard image: {e}")
            dashboard_image_label.setText("Image not available")

        # Center the image using QHBoxLayout
        image_layout = QHBoxLayout()
        image_layout.addStretch()
        image_layout.addWidget(dashboard_image_label)
        image_layout.addStretch()

        main_layout.addLayout(image_layout)  # Add the centered image to the main layout

        dashboard_tab.setLayout(main_layout)
        self.tabs.addTab(dashboard_tab, "Dashboard & User Info")

    def refresh_panel_info(self):
        try:
            # Fetch panels associated with the user
            panels = contract.functions.displayPanels().call({'from': self.user_address})

            # Clear existing items
            self.panel_dropdown.clear()

            if len(panels) > 0:
                # Add panels to the dropdown list
                for panel in panels:
                    panel_id = panel[0]
                    panel_name = f"ID: {panel_id}, Location: {panel[2]}"
                    self.panel_dropdown.addItem(panel_name, userData=panel)

                # Connect the dropdown selection change to a function to display the selected panel info
                self.panel_dropdown.currentIndexChanged.connect(self.display_selected_panel_info)

                # Display information for the initially selected panel
                self.display_selected_panel_info()
            else:
                self.panel_info_label.setText("No Panels Registered")
        except Exception as e:
            logging.error(f"Error fetching panel information: {e}")
            self.panel_info_label.setText("N/A")

    def display_selected_panel_info(self):
        panel_data = self.panel_dropdown.currentData()

        if panel_data:
            panel_id = panel_data[0]
            capacity = panel_data[1]
            energy_balance = panel_data[5]
            efficiency = panel_data[6]

            # Display the selected panel's information
            panel_info_text = (f"Panel ID: {panel_id}, Capacity: {capacity} kWh, "
                               f"Energy Balance: {energy_balance} kWh, Efficiency: {efficiency}%")
            self.panel_info_label.setText(panel_info_text)

            # Update the energy level bar
            energy_percentage = int((energy_balance / capacity) * 100) if capacity > 0 else 0
            self.energy_level_bar.setValue(energy_percentage)

            # Update the panel status label based on efficiency
            self.update_panel_status(efficiency)
        else:
            self.panel_info_label.setText("No panel selected or no panels available.")
            self.energy_level_bar.setValue(0)

    def update_panel_status(self, efficiency):
        if efficiency >= 80:
            color = "green"
            status = "Active"
        elif 50 <= efficiency < 80:
            color = "yellow"
            status = "Moderate"
        else:
            color = "red"
            status = "Low Efficiency"

        # Update the panel status label
        self.panel_status_label.setText(f"Panel Status: {status}")
        self.panel_status_label.setStyleSheet(
            f"background-color: {color}; color: white; padding: 5px; border-radius: 5px;")

    def create_buy_and_sell_tab(self):
        buy_and_sell_tab = QWidget()
        layout = QVBoxLayout()

        # Add the exchange rate label with a larger font size
        exchange_rate_label = QLabel("The price of converting 1 Solar Energy (SEG) to ETH is ETH0.071015 today.")
        font_large = QFont("Arial", 11)  # Set font size to 11
        exchange_rate_label.setFont(font_large)  # Apply larger font size
        exchange_rate_label.setStyleSheet("font-weight: bold; color: black;")
        layout.addWidget(exchange_rate_label)

        # Buy Section with bold font
        buy_section_label = QLabel("Buy Energy")
        font = QFont("Arial", 11)  # Set font size to 11
        buy_section_label.setFont(font)  # Apply bold font
        layout.addWidget(buy_section_label)

        self.offer_list = QListWidget()

        try:
            sales = contract.functions.getAvailableEnergySales().call()
            for sale in sales:
                item_text = (
                    f"Seller: {sale[0]}, Amount: {sale[2]} kWh, Price: {web3.from_wei(sale[3], 'ether')} ETH")
                item = QListWidgetItem(item_text)
                font = QFont("Arial", 11)  # Set the font size to 11 points
                item.setFont(font)
                self.offer_list.addItem(item)

        except Exception as e:
            logging.error(f"Error fetching available energy sales: {e}")
            self.offer_list.addItem("Failed to load offers")

        layout.addWidget(self.offer_list)

        # Add the Sort and Buy buttons in a horizontal layout
        button_layout = QHBoxLayout()

        sort_button = QPushButton("Sort")
        sort_button.setFixedSize(250, 30)  # Adjust the size to make the button larger
        font_button = QFont("Arial", 11)  # Set font size to 11
        sort_button.setFont(font_button)  # Apply the font to the sort button
        sort_button.clicked.connect(self.sort_offers)
        button_layout.addWidget(sort_button)

        buy_button = QPushButton("Buy Energy")
        buy_button.setFixedSize(250, 30)  # Adjust the size to make the button larger
        buy_button.setFont(font_button)  # Apply the font to the buy button
        buy_button.clicked.connect(self.buy_energy)
        button_layout.addWidget(buy_button)

        layout.addLayout(button_layout)

        # Separator
        separator = QLabel("")
        separator.setFixedHeight(20)
        layout.addWidget(separator)

        # Sell Section
        sell_section_label = QLabel("Sell Energy")
        sell_section_label.setFont(font_button)  # Apply the font to the sell section label
        layout.addWidget(sell_section_label)

        self.sell_amount = QDoubleSpinBox()
        self.sell_amount.setDecimals(2)  # Allow up to 2 decimal places
        self.sell_amount.setMaximum(9999.99)  # Adjust the maximum value as needed
        self.sell_amount.setSuffix(" kWh")
        self.sell_amount.setFont(font_button)  # Apply the font to the sell amount spin box
        layout.addWidget(self.sell_amount)

        self.sell_price = QDoubleSpinBox()
        self.sell_price.setDecimals(2)
        self.sell_price.setMaximum(9999.99)  # Adjust the maximum value as needed
        self.sell_price.setSuffix(" ETH")
        self.sell_price.setFont(font_button)  # Apply the font to the sell price spin box
        layout.addWidget(self.sell_price)

        sell_button = QPushButton("Sell Energy")
        sell_button.setFixedSize(750, 30)  # Adjust the size to make the button larger
        sell_button.setFont(font_button)  # Apply the font to the sell button
        sell_button.clicked.connect(self.sell_energy)
        layout.addWidget(sell_button)

        buy_and_sell_tab.setLayout(layout)
        self.tabs.addTab(buy_and_sell_tab, "Buy & Sell Energy")

    def sort_offers(self):
        options = [
            "Lowest Price to Highest",
            "Highest Price to Lowest",
            "Lowest Amount to Highest",
            "Highest Amount to Lowest"
        ]
        sort_option, ok = QInputDialog.getItem(self, "Sort Offers", "Sort by:", options, 0, False)

        if ok and sort_option:
            self.offer_list.clear()

            try:
                sales = contract.functions.getAvailableEnergySales().call()

                if sort_option == "Lowest Price to Highest":
                    sorted_sales = sorted(sales, key=lambda x: x[3])
                elif sort_option == "Highest Price to Lowest":
                    sorted_sales = sorted(sales, key=lambda x: x[3], reverse=True)
                elif sort_option == "Lowest Amount to Highest":
                    sorted_sales = sorted(sales, key=lambda x: x[2])
                elif sort_option == "Highest Amount to Lowest":
                    sorted_sales = sorted(sales, key=lambda x: x[2], reverse=True)

                for sale in sorted_sales:
                    item_text = (
                        f"Seller: {sale[0]}, Amount: {sale[2]} kWh, Price: {web3.from_wei(sale[3], 'ether')} ETH")
                    item = QListWidgetItem(item_text)
                    font = QFont("Arial", 11)  # Set the font size to 11 points
                    item.setFont(font)
                    self.offer_list.addItem(item)
            except Exception as e:
                logging.error(f"Error sorting offers: {e}")
                self.offer_list.addItem("Failed to sort offers")

    def buy_energy(self):
        try:
            sale_index = self.offer_list.currentRow()
            if sale_index < 0:
                QMessageBox.warning(self, "No Selection", "Please select an energy offer to purchase.")
                return

            # Fetch the selected sale
            sales = contract.functions.getAvailableEnergySales().call()
            selected_sale = sales[sale_index]

            # Check if the logged-in user is the same as the seller
            if selected_sale[1] == self.user_address:
                QMessageBox.warning(self, "Invalid Purchase", "You cannot buy energy from yourself.")
                return

            # Calculate the total price based on the amount
            amount = selected_sale[2]
            total_price = selected_sale[3] * amount // selected_sale[2]

            # Execute the purchase transaction and send the corresponding amount of ETH
            tx_hash = contract.functions.buyEnergy(sale_index, int(amount)).transact({
                'from': self.user_address,
                'value': int(total_price)  # Send ETH equal to the calculated price
            })
            web3.eth.wait_for_transaction_receipt(tx_hash)
            QMessageBox.information(self, "Purchase Successful", "Energy purchased successfully!")

            # Refresh the balance label to update the user's ETH balance
            self.refresh_balance()

            # After purchase, prompt the user to allocate energy to panels
            self.allocate_energy(int(amount))

            # Refresh the offers list, dashboard, and history after purchase
            self.refresh_offers()
            self.refresh_panel_info()
            self.refresh_history()

        except Exception as e:
            logging.error(f"Error buying energy: {e}")
            QMessageBox.critical(self, "Purchase Failed",
                                 f"An error occurred while trying to purchase energy: {str(e)}")

    def refresh_balance(self):
        try:
            # Update the balance label with the current balance
            balance = web3.from_wei(web3.eth.get_balance(self.user_address), 'ether')
            self.balance_label.setText(f"{balance} ETH")
        except Exception as e:
            logging.error(f"Error refreshing balance: {e}")

    def refresh_offers(self):
        self.offer_list.clear()
        try:
            sales = contract.functions.getAvailableEnergySales().call()
            for sale in sales:
                item_text = (
                    f"Seller: {sale[0]}, Amount: {sale[2]} kWh, Price: {web3.from_wei(sale[3], 'ether')} ETH")
                item = QListWidgetItem(item_text)
                font = QFont("Arial", 11)  # Set the font size to 11 points
                item.setFont(font)
                self.offer_list.addItem(item)
        except Exception as e:
            logging.error(f"Error fetching available energy sales: {e}")
            self.offer_list.addItem("Failed to load offers")

    def allocate_energy(self, amount):
        try:
            panels = contract.functions.displayPanels().call({'from': self.user_address})
            if len(panels) == 0:
                QMessageBox.warning(self, "No Panels", "You do not have any panels to allocate energy to.")
                return

            for panel in panels:

                panel_id = panel[0]
                panel_name = f"Panel {panel_id} at {panel[2]}"
                panel_capacity = panel[1]
                panel_energy_balance = panel[5]  # Assuming this is the current energy balance of the panel
                remaining_capacity = panel_capacity - panel_energy_balance
                max_allocatable_energy = min(amount, remaining_capacity)
                energy_to_allocate, ok = QInputDialog.getDouble(self, f"Allocate Energy to {panel_name}",
                                                                f"How much energy (kWh) do you want to allocate to {panel_name}? (Max: {max_allocatable_energy} kWh)",
                                                                min=0, max=max_allocatable_energy)
                if ok and energy_to_allocate > 0:
                    # Convert panel_id and energy_to_allocate to the correct type
                    panel_id = int(panel_id)
                    energy_to_allocate = int(energy_to_allocate)

                    # Call the allocateEnergyToPanel function with the correct types
                    tx_hash = contract.functions.allocateEnergyToPanel(panel_id, energy_to_allocate).transact(
                        {'from': self.user_address})
                    web3.eth.wait_for_transaction_receipt(tx_hash)
                    amount -= energy_to_allocate
                    if amount <= 0:
                        break

            if amount > 0:
                QMessageBox.information(self, "Unallocated Energy", f"{amount} kWh could not be allocated.")

            # Refresh the panel info after allocation
            self.refresh_panel_info()

        except Exception as e:
            logging.error(f"Error allocating energy: {e}")
            QMessageBox.critical(self, "Allocation Failed", f"An error occurred while allocating energy: {str(e)}")

    def sell_energy(self):
        try:
            amount = self.sell_amount.value()
            price = self.sell_price.value()

            if amount <= 0 or price <= 0:
                QMessageBox.warning(self, "Invalid Inputs", "Please enter valid amounts for energy and price.")
                return

            # Get user panels
            panels = contract.functions.displayPanels().call({'from': self.user_address})
            if len(panels) == 0:
                QMessageBox.warning(self, "No Panels", "You do not have any panels to sell energy from.")
                return

            # Allow user to select a panel
            panel_items = [f"Panel ID: {panel[0]} at {panel[2]}" for panel in panels]
            panel_choice, ok = QInputDialog.getItem(self, "Select Panel", "Choose a panel to sell energy from:",
                                                    panel_items, 0, False)
            if not ok or not panel_choice:
                return

            selected_panel_index = panel_items.index(panel_choice)
            selected_panel = panels[selected_panel_index]

            if amount > selected_panel[5]:  # Check if the selected panel has enough energy
                QMessageBox.warning(self, "Insufficient Energy",
                                    f"The selected panel only has {selected_panel[5]} kWh available.")
                return

            # Post the energy for sale
            tx_hash = contract.functions.postEnergyForSale(int(amount), web3.to_wei(price, 'ether')).transact(
                {'from': self.user_address})
            web3.eth.wait_for_transaction_receipt(tx_hash)

            # Here, instead of trying to modify the tuple, you could directly call a contract function to adjust the balance
            contract.functions.reduceEnergyBalance(selected_panel[0], int(amount)).transact({'from': self.user_address})

            QMessageBox.information(self, "Sale Successful", "Energy sale posted successfully!")

            # Refresh the buy tab to show the new offer
            self.refresh_offers()
            self.refresh_panel_info()

        except Exception as e:
            logging.error(f"Error selling energy: {e}")
            QMessageBox.critical(self, "Sale Failed", f"An error occurred while trying to sell energy: {str(e)}")

    def create_history_tab(self):
        history_tab = QWidget()
        layout = QVBoxLayout()

        # Set a larger font size
        font = QFont("Arial", 11)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Transaction ID", "Type", "Amount", "Price", "Timestamp"])
        self.history_table.setFont(font)  # Apply the font to the table
        self.history_table.horizontalHeader().setFont(font)  # Apply the font to the table headers
        layout.addWidget(self.history_table)

        self.refresh_history()

        refresh_button = QPushButton("Refresh History")
        refresh_button.setFont(font)  # Apply the font to the button
        refresh_button.clicked.connect(self.refresh_history)
        layout.addWidget(refresh_button)

        history_tab.setLayout(layout)
        self.tabs.addTab(history_tab, "History")

    def refresh_history(self):
        try:
            transactions = contract.functions.displayTransactions().call({'from': self.user_address})
            self.history_table.setRowCount(len(transactions))
            for i, tx in enumerate(transactions):
                # Set a larger font size for each item
                font = QFont("Arial", 11)

                item_id = QTableWidgetItem(str(i))
                item_id.setFont(font)
                self.history_table.setItem(i, 0, item_id)  # Assuming transaction ID is index

                item_type = QTableWidgetItem("Produced" if tx[2] > 0 else "Consumed")
                item_type.setFont(font)
                self.history_table.setItem(i, 1, item_type)

                item_amount = QTableWidgetItem(str(tx[2] if tx[2] > 0 else tx[3]))
                item_amount.setFont(font)
                self.history_table.setItem(i, 2, item_amount)

                item_price = QTableWidgetItem(str(web3.from_wei(tx[4], 'ether')))
                item_price.setFont(font)
                self.history_table.setItem(i, 3, item_price)

                item_timestamp = QTableWidgetItem(str(tx[5]))
                item_timestamp.setFont(font)
                self.history_table.setItem(i, 4, item_timestamp)
        except Exception as e:
            logging.error(f"Error fetching transaction history: {e}")
            QMessageBox.critical(self, "History Fetch Failed", "An error occurred while fetching transaction history.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    while True:
        login_window = LoginWindow()
        if login_window.exec_() == QDialog.Accepted:
            user_address = login_window.user_address  # Retrieve the logged-in user's address from the login window
            is_manager = login_window.manager
            main_window = SolarEnergySystem(user_address=user_address, is_manager=is_manager)
            main_window.show()
            app.exec_()  # Start the application's event loop after login
        else:
            break
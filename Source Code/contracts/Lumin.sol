// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnergyManagement {
    struct Panel {
        uint256 id;
        uint256 capacity; // in kW
        string location;
        uint256 producedEnergy;
        uint256 consumedEnergy;
        uint256 energyBalance; // New variable to store energy balance
        uint256 efficiency; // New variable to store panel efficiency
        address owner;
    }

    struct Transaction {
        string from;  // Store the name of the user
        string to;
        uint256 energyProduced;
        uint256 energyConsumed;
        uint256 tokensTransferred;
        uint256 timestamp;
    }

    struct EnergySale {
        string sellerName;
        address sellerAddress;
        uint256 energy;    // Amount of energy for sale (in kWh)
        uint256 price;     // Price for the energy (in wei)
    }

    struct User {
        string username;
        string actualName;
        bytes32 passwordHash;  // Store hashed password as bytes32
        bool registered;
        bool isManager;
    }

    mapping(address => User) public users;
    mapping(address => Panel[]) public userPanels;
    mapping(address => Transaction[]) public userTransactions;
    mapping(address => uint256) public balances;
    mapping(address => address[]) public managerToUsers; // Mapping from manager to their users
    EnergySale[] public energySales;

    uint256 public panelCount = 0;

    // Register a new user with username, actual name, hashed password, and role
    function register(string memory _username, string memory _actualName, bytes32 _passwordHash, bool _isManager) public {
        require(!users[msg.sender].registered, "User already registered");
        users[msg.sender] = User(_username, _actualName, _passwordHash, true, _isManager);

        // Initialize the user's token balance if required (for token-based transactions)
        balances[msg.sender] = 1000; // Example: 1000 tokens
    }

    // Register a manager and assign users to them
    function registerManagerWithUsers(string memory _username, string memory _actualName, bytes32 _passwordHash, address[] memory _users) public {
        register(_username, _actualName, _passwordHash, true);
        managerToUsers[msg.sender] = _users;
    }

    // Function to add a panel to a user's array of panels
    function addPanelToUser(
        address _user,
        uint256 _id,
        uint256 _capacity,
        string memory _location,
        uint256 _producedEnergy,
        uint256 _consumedEnergy,
        uint256 _efficiency // Add efficiency parameter
    ) public {
        require(users[_user].registered, "User must be registered to add a panel");

        uint256 initialEnergyBalance = _producedEnergy > _consumedEnergy ? _producedEnergy - _consumedEnergy : 0;

        userPanels[_user].push(Panel({
            id: _id,
            capacity: _capacity,
            location: _location,
            producedEnergy: _producedEnergy,
            consumedEnergy: _consumedEnergy,
            energyBalance: initialEnergyBalance, // Initialize energyBalance with producedEnergy - consumedEnergy
            efficiency: _efficiency, // Initialize efficiency
            owner: _user
        }));
        panelCount++;
    }

    // Login function
    function login(string memory _username, bytes32 _passwordHash) public view returns (bool) {
        User memory user = users[msg.sender];
        require(user.registered, "User not registered");
        require(keccak256(abi.encodePacked(user.username)) == keccak256(abi.encodePacked(_username)), "Invalid username");
        require(user.passwordHash == _passwordHash, "Invalid password");
        return true;
    }

    // Function to post energy for sale
    function postEnergyForSale(uint256 _energy, uint256 _price) public {
        require(users[msg.sender].registered, "User must be logged in to post energy for sale");

        // Calculate total available energy
        uint256 totalAvailableEnergy = 0;
        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            totalAvailableEnergy += userPanels[msg.sender][i].energyBalance;
        }
        
        require(_energy <= totalAvailableEnergy, "Not enough energy available in your panels to sell");

        string memory sellerName = users[msg.sender].username;
        energySales.push(EnergySale(sellerName, msg.sender, _energy, _price));
    }

    // Function to buy energy (payable to accept ETH)
    function buyEnergy(uint256 saleIndex, uint256 _amount) public payable {
        require(saleIndex < energySales.length, "Invalid sale index");
        require(users[msg.sender].registered, "User must be logged in to buy energy");
        EnergySale memory sale = energySales[saleIndex];

        require(_amount <= sale.energy, "Amount exceeds available energy for sale");

        // Calculate the total price in Wei for the requested amount
        uint256 totalPrice = sale.price * _amount / sale.energy;
        require(msg.value >= totalPrice, "Insufficient ETH sent");

        // Transfer the ETH from the buyer to the seller
        payable(sale.sellerAddress).transfer(totalPrice);

        // Update the sale
        sale.energy -= _amount;
        if (sale.energy == 0) {
            // Remove the sale from the list if all energy is bought
            for (uint256 i = saleIndex; i < energySales.length - 1; i++) {
                energySales[i] = energySales[i + 1];
            }
            energySales.pop();
        } else {
            energySales[saleIndex] = sale;
        }

        // Record the transaction
        string memory buyerName = users[msg.sender].username;
        userTransactions[msg.sender].push(Transaction(buyerName, sale.sellerName, 0, _amount, totalPrice, block.timestamp));
        userTransactions[sale.sellerAddress].push(Transaction(sale.sellerName, buyerName, _amount, 0, totalPrice, block.timestamp));
    }

    // Function to record energy production
    function produceEnergy(uint256 _panelId, uint256 _energy) public {
        require(users[msg.sender].registered, "User must be logged in to produce energy");
        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            if (userPanels[msg.sender][i].id == _panelId) {
                require(userPanels[msg.sender][i].energyBalance + _energy <= userPanels[msg.sender][i].capacity, "Exceeds panel capacity");
                userPanels[msg.sender][i].producedEnergy += _energy;
                userPanels[msg.sender][i].energyBalance += _energy;
                string memory producerName = users[msg.sender].username;
                userTransactions[msg.sender].push(Transaction(producerName, "", _energy, 0, 0, block.timestamp));
                break;
            }
        }
    }

    // Function to record energy consumption
    function consumeEnergy(uint256 _panelId, uint256 _energy) public {
        require(users[msg.sender].registered, "User must be logged in to consume energy");
        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            if (userPanels[msg.sender][i].id == _panelId) {
                require(userPanels[msg.sender][i].energyBalance >= _energy, "Not enough energy in the panel");
                userPanels[msg.sender][i].consumedEnergy += _energy;
                userPanels[msg.sender][i].energyBalance -= _energy;
                string memory consumerName = users[msg.sender].username;
                userTransactions[msg.sender].push(Transaction(consumerName, "", 0, _energy, 0, block.timestamp));
                break;
            }
        }
    }

    // Function to display total energy history
    function displayTotalEnergyHistory() public view returns (uint256 produced, uint256 consumed) {
        require(users[msg.sender].registered, "User must be logged in to view energy history");
        produced = 0;
        consumed = 0;
        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            produced += userPanels[msg.sender][i].producedEnergy;
            consumed += userPanels[msg.sender][i].consumedEnergy;
        }
    }

    function displayTransactions() public view returns (Transaction[] memory) {
        require(users[msg.sender].registered, "User must be logged in to view transactions");
        
        // Fetch all transactions for the logged-in user
        return userTransactions[msg.sender];
    }

    // Function to display all panels
    function displayPanels() public view returns (Panel[] memory) {
        require(users[msg.sender].registered, "User must be logged in to view panels");
        return userPanels[msg.sender];
    }

    // Function to get available energy sales
    function getAvailableEnergySales() public view returns (EnergySale[] memory) {
        return energySales;
    }

    // Function to allocate purchased energy to specific panels
    function allocateEnergyToPanel(uint256 panelId, uint256 energyAmount) public {
        require(users[msg.sender].registered, "User must be logged in to allocate energy");
        require(energyAmount > 0, "Energy amount must be greater than 0");

        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            if (userPanels[msg.sender][i].id == panelId) {
                require(userPanels[msg.sender][i].energyBalance + energyAmount <= userPanels[msg.sender][i].capacity, "Exceeds panel capacity");
                userPanels[msg.sender][i].producedEnergy += energyAmount;
                userPanels[msg.sender][i].energyBalance += energyAmount;
                return;
            }
        }
        revert("Panel not found");
    }

    // Function to reduce energy balance after posting a sale
    function reduceEnergyBalance(uint256 panelId, uint256 amount) public {
        require(users[msg.sender].registered, "User must be logged in to update energy balance");
        
        for (uint256 i = 0; i < userPanels[msg.sender].length; i++) {
            if (userPanels[msg.sender][i].id == panelId) {
                require(userPanels[msg.sender][i].energyBalance >= amount, "Not enough energy in the panel");
                userPanels[msg.sender][i].energyBalance -= amount;
                return;
            }
        }
        revert("Panel not found");
    }

    // Function to display all panels for a manager
    function displayManagedPanels() public view returns (Panel[] memory) {
        require(users[msg.sender].isManager, "Only a manager can view all panels");

        address[] memory managedUsers = managerToUsers[msg.sender];
        uint256 totalPanels = 0;

        // Calculate total panels managed by this manager
        for (uint256 i = 0; i < managedUsers.length; i++) {
            totalPanels += userPanels[managedUsers[i]].length;
        }

        Panel[] memory panels = new Panel[](totalPanels);
        uint256 counter = 0;

        // Populate the array with panels from all managed users
        for (uint256 i = 0; i < managedUsers.length; i++) {
            for (uint256 j = 0; j < userPanels[managedUsers[i]].length; j++) {
                panels[counter] = userPanels[managedUsers[i]][j];
                counter++;
            }
        }

        return panels;
    }

    // Function to display all transactions for a manager
    function displayManagedTransactions() public view returns (Transaction[] memory) {
        require(users[msg.sender].isManager, "Only a manager can view all transactions");

        address[] memory managedUsers = managerToUsers[msg.sender];
        uint256 totalTransactions = 0;

        // Calculate total transactions managed by this manager
        for (uint256 i = 0; i < managedUsers.length; i++) {
            totalTransactions += userTransactions[managedUsers[i]].length;
        }

        Transaction[] memory transactions = new Transaction[](totalTransactions);
        uint256 counter = 0;

        // Populate the array with transactions from all managed users
        for (uint256 i = 0; i < managedUsers.length; i++) {
            for (uint256 j = 0; j < userTransactions[managedUsers[i]].length; j++) {
                transactions[counter] = userTransactions[managedUsers[i]][j];
                counter++;
            }
        }

        return transactions;
    }
}

const EnergyManagement = artifacts.require("EnergyManagement");

module.exports = async function(deployer, network, accounts) {
    await deployer.deploy(EnergyManagement);
    const instance = await EnergyManagement.deployed();

    // Addresses provided by the user
    const alice = accounts[1];
    const bob = accounts[2];
    const dave = accounts[3];
    const eve = accounts[4];
    const carol = accounts[5];

    // Hash passwords using web3.eth.accounts.hashMessage, choose your own passwords and write them between the quotes below
    const passwordHashAlice = web3.utils.keccak256("");
    const passwordHashBob = web3.utils.keccak256("");
    const passwordHashDave = web3.utils.keccak256("");
    const passwordHashEve = web3.utils.keccak256("");
    const passwordHashCarol = web3.utils.keccak256("");

    // Register users with hashed passwords, full names, and roles
    await instance.register("Rawan", "Rawan Ibrahim", passwordHashAlice, false, { from: alice });
    await instance.register("Sara", "Sara Alturk", passwordHashBob, false, { from: bob });
    await instance.register("Sahar", "Sahar Aljimaani", passwordHashDave, false, { from: dave });
    await instance.register("Rama", "Eve Adams", passwordHashEve, false, { from: eve });

    // Register Carol as a manager and assign Alice, Bob, Dave, and Eve to her
    await instance.registerManagerWithUsers("Carol", "Carol Manager", passwordHashCarol, [alice, bob, dave, eve], { from: carol });

    // Convert the initial ETH amount for energy sales into Wei (1 ETH = 10^18 Wei)
    const ethToWei = (ethAmount) => web3.utils.toWei(ethAmount.toString(), 'ether');

    // Add panels for users
    await instance.addPanelToUser(alice, 1, 500, "Location A", 300, 100, 95, { from: alice });
    await instance.addPanelToUser(bob, 2, 600, "Location B", 500, 100, 90, { from: bob });
    await instance.addPanelToUser(dave, 3, 700, "Location C", 400, 300, 85, { from: dave });
    await instance.addPanelToUser(alice, 4, 800, "Location D", 500, 400, 88, { from: alice });
    await instance.addPanelToUser(alice, 5, 600, "Location E", 500, 300, 70, { from: alice });
    await instance.addPanelToUser(alice, 6, 700, "Location F", 600, 100, 75, { from: alice });
    await instance.addPanelToUser(eve, 7, 750, "Location G", 600, 100, 75, { from: eve });


    // Post initial energy sales with prices converted to Wei
    await instance.postEnergyForSale(200, ethToWei(0.1), { from: alice });
    await instance.postEnergyForSale(300, ethToWei(0.15), { from: bob });
};

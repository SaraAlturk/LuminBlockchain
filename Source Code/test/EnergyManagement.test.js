const EnergyManagement = artifacts.require("EnergyManagement");

contract("EnergyManagement", (accounts) => {
  describe("deployment", async () => {
    it("deploys successfully", async () => {
      const instance = await EnergyManagement.deployed();
      const address = instance.address;

      // Assert that the contract has an address (i.e., it was deployed)
      assert.notEqual(address, undefined);
      assert.notEqual(address, null);
      assert.notEqual(address, "");
      assert.notEqual(address, "0x0");
    });
  });
});

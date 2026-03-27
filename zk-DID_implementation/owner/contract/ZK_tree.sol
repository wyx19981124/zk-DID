// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ZKTree {

    uint256[] private tree;

    // Set the array: overwrite the stored array with the input array
    function setTree(uint256[] calldata _tree) external {
        // Clear the existing array
        delete tree;

        // Copy each element from calldata to storage
        for (uint256 i = 0; i < _tree.length; i++) {
            tree.push(_tree[i]);
        }
    }

    // Get the array: return the whole stored array
    function getTree() external view returns (uint256[] memory) {
        return tree;
    }

    // Get the length of the array
    function getLength() external view returns (uint256) {
        return tree.length;
    }

    function getElement(uint256 k) external view returns (uint256) {
        require(k < tree.length, "Index out of range");
        return tree[k];
    }
}

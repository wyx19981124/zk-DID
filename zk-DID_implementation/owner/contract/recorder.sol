// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AccessRecord {
    struct Record {
        string Pseudonym;
        string Device;
        string Operation;
        uint256 Time;
    }

    Record[] private records;


    function writeRecord(string memory _pseudonym, string memory _device, string memory _operation, uint256 _time) public {
        records.push(
            Record({
                Pseudonym: _pseudonym,
                Device: _device,
                Operation: _operation,
                Time: _time
            })
        );
    }


    function readRecord(uint256 index) public view returns (
            string memory,
            string memory,
            string memory,
            uint256
        )
    {
        require(index < records.length, "Index out of range");
        Record memory r = records[index];
        return (r.Pseudonym, r.Device, r.Operation, r.Time);
    }

    function getRecordCount() public view returns (uint256) {
        return records.length;
    }

    function getAllRecords() public view returns (Record[] memory)
    {
        return records;
    }
}

# Autoconfigure IOx App Network Settings

This simple tool gets your IOx app networking configuration automatically on your IOS XE device. You don't need to configure anything in the CLI!

1. Enable NETCONF via webUI on the device (Administration > Management > HTTP/HTTPS/Netconf)
2. Deploy your IOx application via webUI
3. Put all information in data.json
4. Run main.py script
5. Done! - Activate your app

> Standalone executables for Windows & macOS are in the making!

## Getting Started

1. Clone the repository or download main.py and data.json

2. Install the required python libraries

3. Run the script. The instructions on how to edit the data.json is given in the CLI:

```
python main.py
```

### Prerequisites

* Python installed
* IOS XE 17.1.x
* Enabled NETCONF on the device:
	* via CLI: ```device(config)#netconf-yang```
	* via GUI: Administration > Management > HTTP/HTTPS/Netconf

## Supported & Tested Hardware

* IR1101 with IOS XE 17.1.x

## Versioning

**1.0** - Inital release. Configure network settings via NETCONF.

## Authors

* **Florian Pachinger** - *Initial work* - [flopach](https://github.com/flopach)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details


## Further Links

* [Cisco DevNet Website](https://developer.cisco.com)

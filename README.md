# VOLTTRON Lib Topic Tree

This library provides tree data structures for handling topic-based resources in the VOLTTRON™ platform. It includes specialized trees for handling device topics and general message bus topics.

## Features

- **TopicTree**: A generic tree structure for hierarchical topics.
- **DeviceTree**: A specialized tree for VOLTTRON devices and points, including integration with the Configuration Store.
- Support for pruning, querying, and JSON serialization of topic hierarchies.

## Installation

This library is usually installed as a dependency of other VOLTTRON modular components, but can be installed standalone:

```bash
pip install volttron-lib-topic-tree
```

## Requirements

- Python >= 3.10
- treelib >= 1.6.1
- volttron-core >= 2.0.0rc26

# Akave SDK for Python

The Akave SDK for Python provides a simple interface to interact with the Akave platform.

## Installation

You can install the SDK using pip:

```bash
pip install akavesdk
```

## Usage

### Basic Usage

```python
from akavesdk import SDK

# Initialize the SDK
sdk = SDK()

# Use the SDK
# Example: Get file info
file_info = sdk.file_info(bucket_name="my-bucket", file_name="my-file.txt")
print(file_info)
```

### Streaming API Usage

```python
from akavesdk import StreamingAPI

# Initialize the streaming API
streaming_api = StreamingAPI()

# List files in a bucket
files = streaming_api.list_files(bucket_name="my-bucket")
for file in files:
    print(file)

# Get file info
file_info = streaming_api.file_info(bucket_name="my-bucket", file_name="my-file.txt")
print(file_info)
```

## Development

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/akavesdk-py.git
cd akavesdk-py
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run tests:
```bash
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

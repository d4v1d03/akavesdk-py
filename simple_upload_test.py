#!/usr/bin/env python3
"""
Simple upload test for the specified bucket: upload-chunk-test-bucket
"""
import sys
import os
import io
import time
import secrets

sys.path.insert(0, '.')

from akavesdk import SDK as PythonSDK
from akavesdk import SDKError

def main():
    print("🧪 Simple Upload Test")
    print("🪣 Testing with bucket: upload-chunk-test-bucket")
    print("=" * 50)
    
    try:
        # Setup SDK
        print("🔧 Setting up SDK...")
        sdk = PythonSDK(
            address='yucca.akave.ai:5500',
            max_concurrency=10,
            block_part_size=1000000,
            use_connection_pool=True,
            private_key='0xa5c223e956644f1ba11f0dcc6f3df4992184ff3c919223744d0cf1db33dab4d6'
        )
        
        ipc = sdk.ipc()
        print("✅ SDK initialized successfully")
        
        bucket_name = "upload-chunk-test-bucket"
        
        # Check if bucket exists
        print(f"\n🔍 Checking if bucket exists: {bucket_name}")
        bucket = ipc.view_bucket(None, bucket_name)
        
        if bucket:
            print(f"✅ Bucket exists: {bucket.name} (ID: {bucket.id})")
        else:
            print(f"❌ Bucket does not exist, creating it...")
            result = ipc.create_bucket(None, bucket_name)
            if result:
                print(f"✅ Bucket created: {result.name} (ID: {result.id})")
            else:
                print("❌ Failed to create bucket")
                return 1
        
        # Test small file upload
        print(f"\n📤 Testing small file upload...")
        test_file_name = f"simple_test_{int(time.time())}.bin"
        test_data = secrets.token_bytes(1024)  # 1KB
        
        print(f"  📄 File: {test_file_name}")
        print(f"  📏 Size: {len(test_data)} bytes")
        print(f"  🔧 Creating file and uploading data...")
        
        reader = io.BytesIO(test_data)
        
        start_time = time.time()
        result = ipc.upload(None, bucket_name, test_file_name, reader)
        end_time = time.time()
        
        if result:
            print(f"✅ Upload successful!")
            print(f"  🆔 Root CID: {result.root_cid}")
            print(f"  📏 Encoded Size: {result.encoded_size}")
            print(f"  ⏱️  Upload Time: {end_time - start_time:.2f} seconds")
        else:
            print("❌ Upload failed")
            return 1
        
        # Verify file exists
        print(f"\n🔍 Verifying uploaded file...")
        file_info = ipc.file_info(None, bucket_name, test_file_name)
        
        if file_info:
            print(f"✅ File verified!")
            print(f"  📄 Name: {file_info.name}")
            print(f"  🆔 Root CID: {file_info.root_cid}")
            print(f"  📏 Size: {file_info.encoded_size}")
        else:
            print("❌ File verification failed")
            return 1
        
        # List files in bucket
        print(f"\n📋 Listing files in bucket...")
        files = ipc.list_files(None, bucket_name)
        print(f"✅ Found {len(files)} files in bucket:")
        
        for i, file_item in enumerate(files[:5]):  # Show first 5 files
            print(f"  {i+1}. {file_item.name} ({file_item.encoded_size} bytes)")
        
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more files")
        
        print(f"\n🎉 All tests completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        try:
            if 'sdk' in locals():
                sdk.close()
        except:
            pass

if __name__ == "__main__":
    exit(main()) 
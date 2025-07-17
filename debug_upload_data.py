#!/usr/bin/env python3
"""
Debug script to examine what data is being sent to FillChunkBlock
"""
import sys
import time
import secrets
import io
sys.path.insert(0, '.')

from akavesdk import SDK as PythonSDK

def main():
    print("🔍 Debug Upload Data Flow")
    print("=" * 40)
    
    try:
        # Setup SDK
        sdk = PythonSDK(
            address='yucca.akave.ai:5500',
            max_concurrency=10,
            block_part_size=1000000,
            use_connection_pool=True,
            private_key='0xa5c223e956644f1ba11f0dcc6f3df4992184ff3c919223744d0cf1db33dab4d6'
        )
        
        ipc = sdk.ipc()
        
        # Use existing bucket to avoid creating new ones
        bucket_name = "upload-chunk-test-bucket"
        
        print(f"🪣 Using bucket: {bucket_name}")
        
        # Get bucket info
        bucket = ipc.view_bucket(None, bucket_name)
        print(f"📋 Bucket Info:")
        print(f"  Name: {bucket.name}")
        print(f"  ID: {bucket.id}")
        
        # Get bucket from storage contract
        bucket_data = ipc.ipc.storage.get_bucket_by_name(
            {"from": ipc.ipc.auth.address},
            bucket_name
        )
        
        print(f"\n📋 Storage Contract Bucket Data:")
        print(f"  Raw data: {bucket_data}")
        print(f"  bucket[0] (ID): {bucket_data[0].hex() if isinstance(bucket_data[0], bytes) else bucket_data[0]}")
        print(f"  bucket[1] (Name): {bucket_data[1] if len(bucket_data) > 1 else 'N/A'}")
        print(f"  bucket[2] (CreatedAt): {bucket_data[2] if len(bucket_data) > 2 else 'N/A'}")
        print(f"  bucket[3] (Owner): {bucket_data[3] if len(bucket_data) > 3 else 'N/A'}")
        
        # Check if bucket ID from IPC matches bucket ID from storage contract
        ipc_bucket_id = bucket.id
        contract_bucket_id = bucket_data[0].hex() if isinstance(bucket_data[0], bytes) else str(bucket_data[0])
        
        print(f"\n🔍 Bucket ID Comparison:")
        print(f"  IPC Bucket ID: {ipc_bucket_id}")
        print(f"  Contract Bucket ID: {contract_bucket_id}")
        print(f"  Match: {'✅' if ipc_bucket_id == contract_bucket_id else '❌'}")
        
        # The key insight: what bucket ID gets passed to FillChunkBlock?
        # In our code, we use bucket[0] which is the raw storage contract return
        bucket_id_for_upload = bucket_data[0]  # This is what gets passed to upload
        
        print(f"\n📤 Upload Parameters:")
        print(f"  Bucket ID for upload (bucket[0]): {bucket_id_for_upload.hex() if isinstance(bucket_id_for_upload, bytes) else bucket_id_for_upload}")
        print(f"  Bucket ID type: {type(bucket_id_for_upload)}")
        print(f"  Bucket ID length: {len(bucket_id_for_upload) if isinstance(bucket_id_for_upload, bytes) else 'N/A'}")
        
        # Check what address the storage contract thinks owns this bucket
        bucket_owner = bucket_data[3] if len(bucket_data) > 3 else None
        our_address = ipc.ipc.auth.address
        
        print(f"\n🔑 Ownership Verification:")
        print(f"  Contract Owner: {bucket_owner}")
        print(f"  Our Address: {our_address}")
        print(f"  Match: {'✅' if str(bucket_owner).lower() == str(our_address).lower() else '❌'}")
        
        # The critical question: when FillChunkBlock is called with bucket_id_for_upload,
        # does it find the same owner as we expect?
        
        print(f"\n💡 Key Insights:")
        print(f"  1. The bucket ID passed to FillChunkBlock is: {bucket_id_for_upload.hex() if isinstance(bucket_id_for_upload, bytes) else bucket_id_for_upload}")
        print(f"  2. This bucket should be owned by: {bucket_owner}")
        print(f"  3. Our signature is signed by: {our_address}")
        print(f"  4. For upload to work, these must match exactly")
        
        if str(bucket_owner).lower() != str(our_address).lower():
            print(f"\n❌ MISMATCH DETECTED!")
            print(f"   The bucket owner according to storage contract doesn't match our signing address")
            print(f"   This explains why the signature is rejected")
        else:
            print(f"\n🤔 Ownership looks correct, but upload still fails...")
            print(f"   The issue might be in:")
            print(f"   - How FillChunkBlock looks up bucket ownership")
            print(f"   - Signature encoding differences")
            print(f"   - Smart contract state inconsistency")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
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
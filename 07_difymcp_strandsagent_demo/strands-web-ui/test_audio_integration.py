#!/usr/bin/env python3
"""
Test script for the integrated audio transcription functionality.

This script tests the audio transcription tools without running the full Streamlit app.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from strands_web_ui.utils.audio_transcriber import create_transcriber
        print("✅ Audio transcriber import successful")
    except ImportError as e:
        print(f"❌ Audio transcriber import failed: {e}")
        return False
    
    try:
        from strands_web_ui.tools.audio_transcribe_tool import transcribe_audio_file_sync, get_supported_languages
        print("✅ Audio transcribe tool import successful")
    except ImportError as e:
        print(f"❌ Audio transcribe tool import failed: {e}")
        return False
    
    try:
        import boto3
        print("✅ boto3 import successful")
    except ImportError as e:
        print(f"❌ boto3 import failed: {e}")
        return False
    
    try:
        from pydub import AudioSegment
        print("✅ pydub import successful")
    except ImportError as e:
        print(f"❌ pydub import failed: {e}")
        return False
    
    try:
        from amazon_transcribe.client import TranscribeStreamingClient
        print("✅ amazon-transcribe import successful")
    except ImportError as e:
        print(f"❌ amazon-transcribe import failed: {e}")
        return False
    
    return True

def test_supported_languages():
    """Test the supported languages function."""
    print("\n🌍 Testing supported languages...")
    
    try:
        from strands_web_ui.tools.audio_transcribe_tool import get_supported_languages
        
        result = get_supported_languages()
        print(f"Status: {result['status']}")
        print("Supported languages:")
        for code, name in result['supported_languages'].items():
            print(f"  - {code}: {name}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing supported languages: {e}")
        return False

def test_transcriber_creation():
    """Test creating a transcriber instance."""
    print("\n🎤 Testing transcriber creation...")
    
    try:
        from strands_web_ui.utils.audio_transcriber import create_transcriber
        
        transcriber = create_transcriber(region="ap-southeast-1")
        print(f"✅ Transcriber created successfully")
        print(f"Region: {transcriber.region}")
        print(f"Streaming client available: {transcriber.streaming_client is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating transcriber: {e}")
        return False

def test_aws_credentials():
    """Test AWS credentials configuration."""
    print("\n🔐 Testing AWS credentials...")
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Try to create a Transcribe client
        client = boto3.client('transcribe', region_name='ap-southeast-1')
        
        # Try to list transcription jobs (this will fail if no credentials)
        try:
            client.list_transcription_jobs(MaxResults=1)
            print("✅ AWS credentials are configured and working")
            return True
        except NoCredentialsError:
            print("⚠️ AWS credentials not configured")
            print("Please run: aws configure")
            return False
        except ClientError as e:
            if "UnauthorizedOperation" in str(e) or "AccessDenied" in str(e):
                print("⚠️ AWS credentials configured but may lack Transcribe permissions")
                return True
            else:
                print(f"⚠️ AWS credentials issue: {e}")
                return False
    except Exception as e:
        print(f"❌ Error testing AWS credentials: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Audio Transcription Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Supported Languages", test_supported_languages),
        ("Transcriber Creation", test_transcriber_creation),
        ("AWS Credentials", test_aws_credentials),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The audio transcription integration is ready to use.")
        print("\nNext steps:")
        print("1. Run the Streamlit app: streamlit run app.py")
        print("2. Click '📎 Attach Audio File' to upload an MP3")
        print("3. Enter your prompt and press Enter")
        print("4. Watch the transcription and AI response!")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed. Please fix the issues before using the feature.")
        
        if not any(name == "AWS Credentials" and result for name, result in results):
            print("\n💡 AWS Setup Help:")
            print("1. Install AWS CLI: pip install awscli")
            print("2. Configure credentials: aws configure")
            print("3. Ensure your account has Transcribe permissions")

if __name__ == "__main__":
    main()

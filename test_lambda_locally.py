import json
from lambda_function import lambda_handler

class MockContext:
    def __init__(self):
        self.function_name = "test_lambda_function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_lambda_function"
        self.aws_request_id = "test-request-id"

def test_handler():
    print("Testing lambda_handler locally...")

    # Mock event and context
    event = {"test": "event"}
    context = MockContext()

    # Invoke handler
    response = lambda_handler(event, context)

    print(f"Response: {json.dumps(response, indent=2)}")

    # Assertions
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'price' in body
    assert 'timestamp' in body
    assert body['message'] == 'Price check completed successfully'

    print("\n✅ Lambda handler test passed!")

if __name__ == "__main__":
    test_handler()

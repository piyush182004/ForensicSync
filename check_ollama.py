import ollama
import sys

def check_ollama():
    """Check if Ollama is running and which models are available."""
    try:
        # List available models
        models = ollama.list()
        print("Ollama is running!")
        
        if 'models' in models:
            print("\nAvailable models:")
            for model in models['models']:
                print(f" - {model['name']}: {model.get('size', 'size unknown')}")
        else:
            print("\nNo models found. You may need to download models using 'ollama pull <model>'")
            
        # Try to generate a simple response
        print("\nTesting generation with default model...")
        response = ollama.generate(prompt="Hello, how are you?")
        if 'response' in response:
            print("Generation successful! Response received.")
            print("--------------------------------------------------")
            print(response['response'][:100] + "..." if len(response['response']) > 100 else response['response'])
            print("--------------------------------------------------")
            print("Ollama is properly configured!")
        else:
            print("Warning: Received unexpected response format.")
            
        return True
    except Exception as e:
        print(f"Error connecting to Ollama: {str(e)}")
        print("\nPossible issues:")
        print(" 1. Ollama may not be running. Start it with 'ollama serve'")
        print(" 2. Network issue connecting to the Ollama API")
        print(" 3. No models are installed. Install with 'ollama pull llama2'")
        return False

if __name__ == "__main__":
    print("Checking Ollama configuration...")
    success = check_ollama()
    sys.exit(0 if success else 1)

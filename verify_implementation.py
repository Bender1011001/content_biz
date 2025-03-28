"""
Verification script to check that all components from next-steps-and-improvements.md 
have been properly implemented.

This script doesn't test functionality, but verifies that all the required
files and components exist.
"""
import os
import importlib.util
import sys

def check_file_exists(path):
    """Check if a file exists and print the result."""
    exists = os.path.exists(path)
    if exists:
        print(f"✅ {path} exists")
    else:
        print(f"❌ {path} MISSING")
    return exists

def check_module_has_class(module_path, class_name):
    """Check if a module has a specific class."""
    try:
        # Convert file path to module path
        rel_path = module_path.replace(os.sep, ".")
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]  # Remove .py extension
        
        # Import the module
        module = __import__(rel_path, fromlist=[class_name])
        
        # Check if the class exists in the module
        if hasattr(module, class_name):
            print(f"✅ {module_path} contains {class_name}")
            return True
        else:
            print(f"❌ {module_path} MISSING {class_name}")
            return False
    except Exception as e:
        print(f"❌ Error checking {module_path} for {class_name}: {str(e)}")
        return False

def main():
    # Check that the database model files exist
    required_files = [
        "app/services/ai_service.py",
        "app/services/template_service.py",
        "app/services/ab_testing_service.py",
        "app/schemas/templates.py",
        "app/schemas/ab_testing.py",
        "app/api/templates.py",
        "app/api/ab_testing.py",
        "alembic/versions/15204faa64a0_add_model_fields.py",
        "alembic/versions/1a7209015e35_add_ab_testing_and_templates.py",
    ]
    
    print("\n=== Checking Required Files ===")
    missing_files = 0
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files += 1
    
    if missing_files == 0:
        print("\n✅ All required files exist!")
    else:
        print(f"\n❌ {missing_files} required files are missing!")
    
    # Check the models.py file for new models
    print("\n=== Checking Database Models ===")
    models_file = "app/db/models.py"
    
    # Open and read models.py to check for required models
    if os.path.exists(models_file):
        with open(models_file, "r") as f:
            models_content = f.read()
            
        required_models = [
            "ABTest", 
            "ABTestVariant", 
            "ContentTemplate"
        ]
        
        missing_models = 0
        for model in required_models:
            if f"class {model}" in models_content:
                print(f"✅ models.py contains {model} model")
            else:
                print(f"❌ models.py MISSING {model} model")
                missing_models += 1
                
        if missing_models == 0:
            print("\n✅ All required models exist!")
        else:
            print(f"\n❌ {missing_models} required models are missing!")
    else:
        print(f"❌ {models_file} does not exist!")
    
    # Check that the router includes the new endpoints
    print("\n=== Checking API Router ===")
    router_file = "app/api/router.py"
    
    if os.path.exists(router_file):
        with open(router_file, "r") as f:
            router_content = f.read()
            
        if "templates" in router_content and "ab_testing" in router_content:
            print("✅ Router includes templates and ab_testing endpoints")
        else:
            print("❌ Router MISSING templates or ab_testing endpoints")
    else:
        print(f"❌ {router_file} does not exist!")
        
    # Check that crew_service.py has been updated
    print("\n=== Checking Updated Services ===")
    crew_service_file = "app/services/crew_service.py"
    
    if os.path.exists(crew_service_file):
        with open(crew_service_file, "r") as f:
            crew_content = f.read()
            
        if "ModelSelector" in crew_content and "force_model" in crew_content:
            print("✅ crew_service.py has been updated with ModelSelector and force_model")
        else:
            print("❌ crew_service.py MISSING ModelSelector or force_model")
    else:
        print(f"❌ {crew_service_file} does not exist!")
    
    print("\n=== Implementation Verification Complete ===")

if __name__ == "__main__":
    main()

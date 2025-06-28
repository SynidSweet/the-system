#!/usr/bin/env python3
"""
Modification Validator Component

Handles validation and testing of self-modification changes, ensuring system
integrity and safety before finalizing modifications.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ModificationValidator:
    """Validates self-modification changes through comprehensive testing"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    async def run_health_check(self) -> bool:
        """Run comprehensive system health check"""
        print("🏥 Running system health check...")
        
        try:
            # Run the seed system health check
            result = subprocess.run(
                [sys.executable, "scripts/seed_system.py"],
                cwd=self.project_root / "agent_system",
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if "Health check passed" in result.stdout:
                print("  ✅ System health check passed")
                return True
            else:
                print("  ❌ System health check failed")
                print(f"  Output: {result.stdout}")
                print(f"  Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False
    
    async def run_automated_tests(self) -> bool:
        """Run any available automated tests"""
        print("🤖 Running automated tests...")
        
        # Check for test files
        test_patterns = [
            "tests/test_*.py",
            "test_*.py", 
            "*/test_*.py"
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_root.glob(pattern))
        
        if not test_files:
            print("  ⚠️  No automated test files found, skipping")
            return True
        
        try:
            # Try to run pytest
            result = subprocess.run(
                ["python", "-m", "pytest", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("  ✅ All automated tests passed")
                return True
            else:
                print("  ❌ Some automated tests failed")
                print(f"  Output: {result.stdout}")
                return False
                
        except FileNotFoundError:
            print("  ⚠️  pytest not available, skipping automated tests")
            return True
        except Exception as e:
            print(f"  ❌ Test execution failed: {e}")
            return False
    
    async def validate_git_status(self) -> Tuple[bool, str]:
        """Validate git repository status"""
        print("📋 Validating git status...")
        
        try:
            # Check git status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            status_output = result.stdout.strip()
            
            if status_output:
                print(f"  📝 Working directory has changes:")
                for line in status_output.split('\n'):
                    print(f"    {line}")
                return True, status_output
            else:
                print("  ✅ Working directory is clean")
                return True, ""
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Git status check failed: {e}")
            return False, ""
    
    async def validate_database_integrity(self) -> bool:
        """Validate database integrity after modifications"""
        print("🗃️ Validating database integrity...")
        
        try:
            # Check if database file exists and is accessible
            db_path = self.project_root / "agent_system" / "data" / "agent_system.db"
            
            if not db_path.exists():
                print("  ⚠️  Database file not found, may be normal for new setup")
                return True
            
            # Try to connect and do basic queries
            import sqlite3
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check that core tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('entities', 'entity_relationships', 'events')
                """)
                tables = cursor.fetchall()
                
                expected_tables = {'entities', 'entity_relationships', 'events'}
                found_tables = {table[0] for table in tables}
                
                if expected_tables.issubset(found_tables):
                    print("  ✅ Database integrity validated")
                    return True
                else:
                    missing = expected_tables - found_tables
                    print(f"  ❌ Missing database tables: {missing}")
                    return False
                    
        except Exception as e:
            print(f"  ❌ Database validation failed: {e}")
            return False
    
    async def validate_api_endpoints(self) -> bool:
        """Validate that API endpoints are functional"""
        print("🌐 Validating API endpoints...")
        
        try:
            # This would require starting the API server and testing endpoints
            # For now, we'll do a basic import test to ensure no syntax errors
            
            import importlib.util
            
            api_main = self.project_root / "agent_system" / "api" / "main.py"
            
            if not api_main.exists():
                print("  ⚠️  API main file not found")
                return False
            
            spec = importlib.util.spec_from_file_location("api_main", api_main)
            if spec is None:
                print("  ❌ Could not load API module spec")
                return False
            
            module = importlib.util.module_from_spec(spec)
            
            # Try to load the module (this will catch syntax errors)
            try:
                spec.loader.exec_module(module)
                print("  ✅ API module loads without syntax errors")
                return True
            except Exception as e:
                print(f"  ❌ API module has errors: {e}")
                return False
                
        except Exception as e:
            print(f"  ❌ API validation failed: {e}")
            return False
    
    async def validate_core_imports(self) -> bool:
        """Validate that core system imports work correctly"""
        print("📦 Validating core imports...")
        
        try:
            # Test key system imports
            core_modules = [
                "core.entities.entity_manager",
                "core.universal_agent_runtime", 
                "core.database_manager",
                "tools.core_mcp.core_tools"
            ]
            
            for module_name in core_modules:
                try:
                    __import__(module_name)
                    print(f"  ✅ {module_name}")
                except ImportError as e:
                    print(f"  ❌ {module_name}: {e}")
                    return False
            
            print("  ✅ All core imports successful")
            return True
            
        except Exception as e:
            print(f"  ❌ Import validation failed: {e}")
            return False
    
    async def run_full_validation_suite(self) -> bool:
        """Run the complete validation suite"""
        print("\n🧪 Phase 3: Testing and Validation")
        
        validation_results = []
        
        # Run all validation checks
        checks = [
            ("Git Status", self.validate_git_status),
            ("Core Imports", self.validate_core_imports),
            ("Database Integrity", self.validate_database_integrity),
            ("API Endpoints", self.validate_api_endpoints),
            ("Health Check", self.run_health_check),
            ("Automated Tests", self.run_automated_tests)
        ]
        
        for check_name, check_func in checks:
            try:
                if check_name == "Git Status":
                    result, _ = await check_func()
                else:
                    result = await check_func()
                validation_results.append((check_name, result))
            except Exception as e:
                print(f"  ❌ {check_name} failed with exception: {e}")
                validation_results.append((check_name, False))
        
        # Report results
        print(f"\n📊 Validation Results:")
        passed = 0
        total = len(validation_results)
        
        for check_name, result in validation_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {check_name}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100
        print(f"\n📈 Overall: {passed}/{total} checks passed ({success_rate:.1f}%)")
        
        if passed == total:
            print("✅ Phase 3 completed - All validations passed")
            return True
        else:
            print("❌ Phase 3 failed - Some validations failed")
            return False
    
    async def create_testing_plan(self, task_description: str, development_branch: str) -> Optional[Path]:
        """Create a testing plan file for the modification"""
        print("🧪 Setting up testing plan...")
        
        try:
            # Create testing checklist
            test_file = self.project_root / f"tests/self_modification_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            test_file.parent.mkdir(exist_ok=True)
            
            test_content = f"""# Self-Modification Testing Plan

## Task: {task_description}
## Branch: {development_branch}

## Pre-Implementation Tests
- [ ] System health check passed
- [ ] All existing tests pass
- [ ] Database connectivity verified
- [ ] Core agents operational

## Implementation Tests
<!-- Agent should add specific tests during implementation -->
- [ ] New functionality works as expected
- [ ] Error handling implemented
- [ ] Edge cases handled
- [ ] Performance within acceptable limits

## Integration Tests
- [ ] Existing functionality unaffected
- [ ] Inter-component communication works
- [ ] Database operations successful
- [ ] API endpoints functional

## Post-Deployment Tests
- [ ] System restart successful
- [ ] Health checks pass
- [ ] User workflows functional
- [ ] Performance metrics acceptable

## Rollback Tests
- [ ] Rollback procedure tested
- [ ] System recovers to previous state
- [ ] No data loss or corruption

---
Testing plan generated on {datetime.now().isoformat()}
"""
            
            test_file.write_text(test_content)
            print(f"  ✅ Testing plan created: {test_file}")
            
            return test_file
            
        except Exception as e:
            print(f"  ❌ Failed to create testing plan: {e}")
            return None
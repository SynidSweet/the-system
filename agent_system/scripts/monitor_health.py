#!/usr/bin/env python3
"""
Real-time health monitoring for the agent system.

This script provides continuous monitoring of system health, performance,
and operational status. Used during self-modification and normal operation.

Usage:
    python scripts/monitor_health.py                          # Interactive monitoring
    python scripts/monitor_health.py --duration 60           # Monitor for 60 seconds
    python scripts/monitor_health.py --check-once            # Single health check
    python scripts/monitor_health.py --alert-webhook URL     # Send alerts to webhook
"""

import asyncio
import argparse
import sys
import time
import json
import psutil
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import db_manager
from core.database_manager import database


class HealthMonitor:
    """Real-time system health monitoring"""
    
    def __init__(self, alert_webhook: Optional[str] = None):
        self.alert_webhook = alert_webhook
        self.monitoring = False
        self.start_time = None
        self.health_history = []
        self.alert_cooldowns = {}  # Prevent spam alerts
        
        # Health thresholds
        self.thresholds = {
            "cpu_percent": 80.0,      # CPU usage %
            "memory_percent": 85.0,   # Memory usage %
            "disk_percent": 90.0,     # Disk usage %
            "db_response_time": 1.0,  # Database response time (seconds)
            "agent_count": 9,         # Expected agent count
            "error_rate": 0.1         # Error rate threshold
        }
    
    async def start_monitoring(self, duration: Optional[int] = None) -> bool:
        """Start continuous health monitoring"""
        print("🏥 Starting Health Monitoring")
        print("=" * 60)
        print(f"Monitoring thresholds: {self.thresholds}")
        if duration:
            print(f"Duration: {duration} seconds")
        else:
            print("Duration: Continuous (Ctrl+C to stop)")
        print("=" * 60)
        
        self.monitoring = True
        self.start_time = time.time()
        
        try:
            end_time = time.time() + duration if duration else None
            
            while self.monitoring:
                # Perform health check
                health_status = await self._perform_health_check()
                
                # Display status
                self._display_health_status(health_status)
                
                # Check for alerts
                await self._check_alerts(health_status)
                
                # Store in history
                self.health_history.append(health_status)
                
                # Keep only last 100 entries
                if len(self.health_history) > 100:
                    self.health_history.pop(0)
                
                # Check if duration exceeded
                if end_time and time.time() >= end_time:
                    break
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        self.monitoring = False
        
        # Generate final report
        await self._generate_monitoring_report()
        
        return True
    
    async def perform_single_check(self) -> Dict[str, Any]:
        """Perform a single health check"""
        print("🔍 Performing Single Health Check")
        print("=" * 60)
        
        health_status = await self._perform_health_check()
        self._display_health_status(health_status)
        
        # Overall health assessment
        overall_health = health_status["overall_status"]
        if overall_health == "healthy":
            print("\n✅ System is healthy!")
        elif overall_health == "warning":
            print("\n⚠️  System has warnings - review issues above")
        else:
            print("\n❌ System is unhealthy - immediate attention needed")
        
        return health_status
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        timestamp = datetime.now()
        health_status = {
            "timestamp": timestamp.isoformat(),
            "uptime_seconds": time.time() - self.start_time if self.start_time else 0,
            "checks": {},
            "alerts": [],
            "overall_status": "healthy"  # healthy, warning, critical
        }
        
        # System resource checks
        await self._check_system_resources(health_status)
        
        # Database health checks
        await self._check_database_health(health_status)
        
        # Application health checks
        await self._check_application_health(health_status)
        
        # Service availability checks
        await self._check_service_availability(health_status)
        
        # Determine overall status
        self._determine_overall_status(health_status)
        
        return health_status
    
    async def _check_system_resources(self, health_status: Dict[str, Any]):
        """Check system resource utilization"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            health_status["checks"]["cpu_usage"] = {
                "value": cpu_percent,
                "threshold": self.thresholds["cpu_percent"],
                "status": "warning" if cpu_percent > self.thresholds["cpu_percent"] else "ok",
                "message": f"CPU usage: {cpu_percent:.1f}%"
            }
            
            # Memory usage
            memory = psutil.virtual_memory()
            health_status["checks"]["memory_usage"] = {
                "value": memory.percent,
                "threshold": self.thresholds["memory_percent"],
                "status": "warning" if memory.percent > self.thresholds["memory_percent"] else "ok",
                "message": f"Memory usage: {memory.percent:.1f}% ({memory.used/1024/1024/1024:.1f}GB used)"
            }
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            health_status["checks"]["disk_usage"] = {
                "value": disk_percent,
                "threshold": self.thresholds["disk_percent"],
                "status": "warning" if disk_percent > self.thresholds["disk_percent"] else "ok",
                "message": f"Disk usage: {disk_percent:.1f}% ({disk.used/1024/1024/1024:.1f}GB used)"
            }
            
            # Process count
            process_count = len(psutil.pids())
            health_status["checks"]["process_count"] = {
                "value": process_count,
                "status": "ok",
                "message": f"Running processes: {process_count}"
            }
            
        except Exception as e:
            health_status["checks"]["system_resources"] = {
                "status": "error",
                "message": f"Failed to check system resources: {e}"
            }
    
    async def _check_database_health(self, health_status: Dict[str, Any]):
        """Check database connectivity and performance"""
        try:
            # Database connectivity test
            start_time = time.time()
            await db_manager.connect()
            await database.initialize()
            
            # Simple query test
            agents = await database.agents.get_all_active()
            db_response_time = time.time() - start_time
            
            health_status["checks"]["database_connectivity"] = {
                "value": db_response_time,
                "threshold": self.thresholds["db_response_time"],
                "status": "warning" if db_response_time > self.thresholds["db_response_time"] else "ok",
                "message": f"Database responsive in {db_response_time:.3f}s"
            }
            
            # Agent count check
            agent_count = len(agents)
            health_status["checks"]["agent_count"] = {
                "value": agent_count,
                "threshold": self.thresholds["agent_count"],
                "status": "warning" if agent_count < self.thresholds["agent_count"] else "ok",
                "message": f"Active agents: {agent_count}/{self.thresholds['agent_count']}"
            }
            
            # Database size check
            db_path = Path(__file__).parent.parent / "agent_system.db"
            if db_path.exists():
                db_size_mb = db_path.stat().st_size / 1024 / 1024
                health_status["checks"]["database_size"] = {
                    "value": db_size_mb,
                    "status": "ok",
                    "message": f"Database size: {db_size_mb:.1f}MB"
                }
            
        except Exception as e:
            health_status["checks"]["database_health"] = {
                "status": "critical",
                "message": f"Database health check failed: {e}"
            }
    
    async def _check_application_health(self, health_status: Dict[str, Any]):
        """Check application-specific health"""
        try:
            # Tool registry check
            from tools.base_tool import tool_registry
            from tools.core_mcp.core_tools import register_core_tools
            from tools.system_tools.mcp_integrations import register_system_tools
            from tools.system_tools.internal_tools import register_internal_tools
            
            # Register tools to count them
            register_core_tools(tool_registry)
            register_system_tools(tool_registry)
            register_internal_tools(tool_registry)
            
            tools = tool_registry.list_tools()
            total_tools = sum(len(tools) for tools in tools.values())
            
            health_status["checks"]["tool_registry"] = {
                "value": total_tools,
                "status": "ok" if total_tools >= 10 else "warning",
                "message": f"Registered tools: {total_tools}"
            }
            
            # Context documents check
            docs = await database.context_documents.get_all()
            health_status["checks"]["context_documents"] = {
                "value": len(docs),
                "status": "ok" if len(docs) >= 10 else "warning",
                "message": f"Context documents: {len(docs)}"
            }
            
        except Exception as e:
            health_status["checks"]["application_health"] = {
                "status": "error",
                "message": f"Application health check failed: {e}"
            }
    
    async def _check_service_availability(self, health_status: Dict[str, Any]):
        """Check service endpoints availability"""
        try:
            # Check if API server is running (if applicable)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:8000/health', timeout=5) as response:
                        if response.status == 200:
                            health_status["checks"]["api_server"] = {
                                "status": "ok",
                                "message": "API server responding"
                            }
                        else:
                            health_status["checks"]["api_server"] = {
                                "status": "warning",
                                "message": f"API server returned status {response.status}"
                            }
            except aiohttp.ClientError:
                health_status["checks"]["api_server"] = {
                    "status": "info",
                    "message": "API server not running (normal if not started)"
                }
            
            # Check web interface (if applicable)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:3000', timeout=3) as response:
                        if response.status == 200:
                            health_status["checks"]["web_interface"] = {
                                "status": "ok",
                                "message": "Web interface responding"
                            }
                        else:
                            health_status["checks"]["web_interface"] = {
                                "status": "warning",
                                "message": f"Web interface returned status {response.status}"
                            }
            except aiohttp.ClientError:
                health_status["checks"]["web_interface"] = {
                    "status": "info",
                    "message": "Web interface not running (normal if not started)"
                }
                
        except Exception as e:
            health_status["checks"]["service_availability"] = {
                "status": "error",
                "message": f"Service availability check failed: {e}"
            }
    
    def _determine_overall_status(self, health_status: Dict[str, Any]):
        """Determine overall system status based on individual checks"""
        critical_count = 0
        warning_count = 0
        
        for check_name, check_data in health_status["checks"].items():
            status = check_data.get("status", "unknown")
            
            if status == "critical":
                critical_count += 1
                health_status["alerts"].append({
                    "level": "critical",
                    "check": check_name,
                    "message": check_data.get("message", "Critical issue detected")
                })
            elif status == "warning":
                warning_count += 1
                health_status["alerts"].append({
                    "level": "warning", 
                    "check": check_name,
                    "message": check_data.get("message", "Warning condition detected")
                })
            elif status == "error":
                warning_count += 1
                health_status["alerts"].append({
                    "level": "error",
                    "check": check_name,
                    "message": check_data.get("message", "Error during check")
                })
        
        # Determine overall status
        if critical_count > 0:
            health_status["overall_status"] = "critical"
        elif warning_count > 0:
            health_status["overall_status"] = "warning"
        else:
            health_status["overall_status"] = "healthy"
    
    def _display_health_status(self, health_status: Dict[str, Any]):
        """Display health status in terminal"""
        timestamp = health_status["timestamp"][:19].replace('T', ' ')
        overall_status = health_status["overall_status"]
        
        # Status symbol
        status_symbols = {
            "healthy": "✅",
            "warning": "⚠️ ",
            "critical": "❌"
        }
        symbol = status_symbols.get(overall_status, "❓")
        
        print(f"\n{symbol} [{timestamp}] System Status: {overall_status.upper()}")
        
        # Display key metrics in compact format
        metrics = []
        for check_name, check_data in health_status["checks"].items():
            status = check_data.get("status", "unknown")
            message = check_data.get("message", "")
            
            status_icon = {
                "ok": "✅",
                "warning": "⚠️ ",
                "critical": "❌",
                "error": "❌",
                "info": "ℹ️ "
            }.get(status, "❓")
            
            if status in ["warning", "critical", "error"]:
                metrics.append(f"{status_icon} {check_name}: {message}")
            elif check_name in ["cpu_usage", "memory_usage", "database_connectivity"]:
                # Always show key metrics
                metrics.append(f"{status_icon} {check_name}: {message}")
        
        for metric in metrics:
            print(f"  {metric}")
        
        # Show alerts if any
        if health_status["alerts"]:
            print(f"  🚨 {len(health_status['alerts'])} alerts active")
    
    async def _check_alerts(self, health_status: Dict[str, Any]):
        """Check for alert conditions and send notifications"""
        if not self.alert_webhook:
            return
        
        critical_alerts = [alert for alert in health_status["alerts"] if alert["level"] == "critical"]
        
        for alert in critical_alerts:
            alert_key = f"{alert['check']}_{alert['level']}"
            
            # Check cooldown (don't spam alerts)
            if alert_key in self.alert_cooldowns:
                if time.time() - self.alert_cooldowns[alert_key] < 300:  # 5 minute cooldown
                    continue
            
            # Send alert
            await self._send_alert(alert, health_status)
            self.alert_cooldowns[alert_key] = time.time()
    
    async def _send_alert(self, alert: Dict[str, Any], health_status: Dict[str, Any]):
        """Send alert to webhook"""
        try:
            payload = {
                "timestamp": health_status["timestamp"],
                "level": alert["level"],
                "check": alert["check"],
                "message": alert["message"],
                "overall_status": health_status["overall_status"],
                "system": "agent_system_health_monitor"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.alert_webhook, json=payload) as response:
                    if response.status == 200:
                        print(f"🚨 Alert sent: {alert['check']} - {alert['message']}")
                    else:
                        print(f"⚠️  Failed to send alert: HTTP {response.status}")
                        
        except Exception as e:
            print(f"⚠️  Failed to send alert: {e}")
    
    async def _generate_monitoring_report(self):
        """Generate monitoring session report"""
        if not self.health_history:
            return
        
        print("\n" + "=" * 60)
        print("📊 MONITORING SESSION REPORT")
        print("=" * 60)
        
        duration = time.time() - self.start_time if self.start_time else 0
        print(f"Session Duration: {duration:.1f} seconds")
        print(f"Health Checks: {len(self.health_history)}")
        
        # Calculate status distribution
        status_counts = {"healthy": 0, "warning": 0, "critical": 0}
        for health_check in self.health_history:
            status = health_check.get("overall_status", "unknown")
            if status in status_counts:
                status_counts[status] += 1
        
        print(f"Status Distribution:")
        for status, count in status_counts.items():
            percentage = (count / len(self.health_history)) * 100
            print(f"  {status.title()}: {count} ({percentage:.1f}%)")
        
        # Save detailed report
        report_file = Path(__file__).parent.parent / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "session_start": self.start_time,
            "session_duration": duration,
            "health_checks": len(self.health_history),
            "status_distribution": status_counts,
            "thresholds": self.thresholds,
            "history": self.health_history[-10:]  # Keep last 10 for size
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"Detailed report saved: {report_file}")
        
        # Overall assessment
        healthy_percentage = (status_counts["healthy"] / len(self.health_history)) * 100
        if healthy_percentage >= 90:
            print("\n✅ System was stable throughout monitoring period")
        elif healthy_percentage >= 70:
            print("\n⚠️  System had some issues - review warnings")
        else:
            print("\n❌ System was unstable - investigate critical issues")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Real-time health monitoring")
    parser.add_argument("--duration", type=int, help="Monitoring duration in seconds")
    parser.add_argument("--check-once", action="store_true", help="Perform single health check")
    parser.add_argument("--alert-webhook", help="Webhook URL for sending alerts")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    thresholds = {}
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config = json.load(f)
            thresholds = config.get('thresholds', {})
    
    monitor = HealthMonitor(alert_webhook=args.alert_webhook)
    
    # Update thresholds if provided
    if thresholds:
        monitor.thresholds.update(thresholds)
    
    try:
        if args.check_once:
            health_status = await monitor.perform_single_check()
            return health_status["overall_status"] == "healthy"
        else:
            return await monitor.start_monitoring(args.duration)
            
    except Exception as e:
        print(f"❌ Health monitoring failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Health monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Health monitoring failed: {e}")
        sys.exit(1)
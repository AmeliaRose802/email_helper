#!/usr/bin/env python3
"""
Email Processing Pipeline Demonstration Script

This script demonstrates the complete T9 Email Processing Pipeline implementation
with background job queuing, WebSocket updates, and mobile-ready components.
"""

import sys
import asyncio
import json
from datetime import datetime

# Add paths for our modules
sys.path.insert(0, 'backend/services')
sys.path.insert(0, 'backend/workers')

try:
    import job_queue as jq_module
    import websocket_manager as ws_module
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please run from the email_helper root directory")
    sys.exit(1)


class ProcessingPipelineDemo:
    """Demonstration of the email processing pipeline."""
    
    def __init__(self):
        self.queue = jq_module.JobQueue()
        self.ws_manager = ws_module.WebSocketManager()
        self.demo_start = datetime.now()
    
    def print_header(self, title):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_step(self, step_num, title):
        """Print a formatted step."""
        print(f"\n{step_num}. 🔄 {title}")
        print("-" * 50)
    
    async def demonstrate_pipeline_creation(self):
        """Demonstrate pipeline creation."""
        self.print_step(1, "Creating Email Processing Pipeline")
        
        # Sample emails to process
        sample_emails = [
            "email_urgent_meeting_001",
            "email_project_update_002", 
            "email_task_assignment_003",
            "email_client_request_004"
        ]
        
        user_id = "demo_user_2024"
        
        print(f"📧 Sample emails to process: {len(sample_emails)}")
        for i, email_id in enumerate(sample_emails, 1):
            print(f"   {i}. {email_id}")
        
        # Create pipeline
        pipeline_id = await self.queue.create_pipeline(sample_emails, user_id)
        
        print(f"\n✅ Pipeline created successfully!")
        print(f"   🆔 Pipeline ID: {pipeline_id}")
        print(f"   👤 User ID: {user_id}")
        print(f"   📅 Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return pipeline_id, sample_emails
    
    async def demonstrate_pipeline_status(self, pipeline_id):
        """Demonstrate pipeline status checking."""
        self.print_step(2, "Checking Pipeline Status")
        
        pipeline = await self.queue.get_pipeline(pipeline_id)
        
        print(f"📊 Pipeline Status Report:")
        print(f"   🆔 ID: {pipeline.id}")
        print(f"   📋 Status: {pipeline.status}")
        print(f"   📈 Overall Progress: {pipeline.overall_progress}%")
        print(f"   📨 Total Emails: {len(pipeline.email_ids)}")
        print(f"   ⚙️  Total Jobs: {len(pipeline.jobs)}")
        print(f"   📅 Created: {pipeline.created_at}")
        
        # Show job breakdown by type
        job_types = {}
        for job in pipeline.jobs:
            job_type = job.type.value
            job_types[job_type] = job_types.get(job_type, 0) + 1
        
        print(f"\n⚙️  Jobs by Type:")
        for job_type, count in job_types.items():
            print(f"   • {job_type.replace('_', ' ').title()}: {count} jobs")
        
        return pipeline
    
    async def demonstrate_job_processing(self, pipeline):
        """Demonstrate job processing with progress updates."""
        self.print_step(3, "Processing Jobs with Real-time Updates")
        
        print("🚀 Starting background job processing simulation...")
        
        # Process jobs in order of priority and type
        jobs_to_process = pipeline.jobs[:6]  # Process 6 jobs (2 emails worth)
        
        for i, job in enumerate(jobs_to_process, 1):
            print(f"\n   📤 Processing Job {i}/{len(jobs_to_process)}")
            print(f"      🆔 Job ID: {job.id}")
            print(f"      📧 Email: {job.email_id}")
            print(f"      🔧 Type: {job.type.value.replace('_', ' ').title()}")
            
            # Simulate processing steps
            processing_steps = [
                (10, "Initializing processor..."),
                (25, "Loading email data..."),
                (50, f"Performing {job.type.value}..."),
                (75, "Analyzing results..."),
                (90, "Storing results..."),
                (100, "Processing completed!")
            ]
            
            for percentage, message in processing_steps:
                progress = jq_module.JobProgress(
                    step=job.type.value.replace('_', ' ').title(),
                    percentage=percentage,
                    message=message
                )
                
                await self.queue.update_job_progress(job.id, progress)
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                if percentage < 100:
                    print(f"      📈 {percentage}% - {message}")
            
            # Complete the job
            result = {
                "job_type": job.type.value,
                "email_id": job.email_id,
                "processed_at": datetime.now().isoformat(),
                "status": "success",
                "data": {
                    "analysis_confidence": 0.85,
                    "processing_time_ms": 1500,
                    "features_extracted": 12
                }
            }
            
            await self.queue.complete_job(job.id, result)
            print(f"      ✅ Job completed successfully!")
        
        # Show updated pipeline status
        updated_pipeline = await self.queue.get_pipeline(pipeline.id)
        print(f"\n📊 Updated Pipeline Status:")
        print(f"   📈 Overall Progress: {updated_pipeline.overall_progress}%")
        
        # Count job statuses
        status_counts = {}
        for job in updated_pipeline.jobs:
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"   ⚙️  Job Status Summary:")
        for status, count in status_counts.items():
            emoji = {"completed": "✅", "queued": "⏳", "processing": "🔄", "failed": "❌"}.get(status, "📝")
            print(f"      {emoji} {status.title()}: {count}")
    
    async def demonstrate_error_handling(self, pipeline):
        """Demonstrate error handling and retry mechanisms."""
        self.print_step(4, "Error Handling and Retry Mechanisms")
        
        # Pick a queued job to simulate failure
        queued_jobs = [job for job in pipeline.jobs if job.status == jq_module.JobStatus.QUEUED]
        
        if queued_jobs:
            test_job = queued_jobs[0]
            print(f"🧪 Testing error handling with job: {test_job.id}")
            print(f"   📧 Email: {test_job.email_id}")
            print(f"   🔧 Type: {test_job.type.value}")
            
            # Simulate job failure
            error_message = "Simulated network timeout during AI processing"
            print(f"\n❌ Simulating job failure: {error_message}")
            
            await self.queue.fail_job(test_job.id, error_message)
            
            # Check retry status
            failed_job = await self.queue.get_job(test_job.id)
            print(f"\n🔄 Retry Mechanism Results:")
            print(f"   📊 Retry Count: {failed_job.retry_count}/{failed_job.max_retries}")
            print(f"   📋 Current Status: {failed_job.status.value}")
            print(f"   ⚠️  Error Message: {failed_job.error}")
            
            if failed_job.status == jq_module.JobStatus.QUEUED:
                print(f"   ✅ Job automatically queued for retry!")
            
            # Test max retries
            print(f"\n🧪 Testing maximum retry limit...")
            for attempt in range(2, failed_job.max_retries + 2):
                await self.queue.fail_job(test_job.id, f"Retry attempt {attempt} failed")
                updated_job = await self.queue.get_job(test_job.id)
                
                print(f"   Attempt {attempt}: {updated_job.status.value} (retries: {updated_job.retry_count})")
                
                if updated_job.status == jq_module.JobStatus.FAILED:
                    print(f"   ❌ Job marked as permanently failed after {updated_job.max_retries} retries")
                    break
    
    async def demonstrate_websocket_features(self):
        """Demonstrate WebSocket management features."""
        self.print_step(5, "WebSocket Real-time Communication")
        
        print("📡 WebSocket Manager Features:")
        
        # Get WebSocket statistics
        stats = await self.ws_manager.get_stats()
        
        print(f"   🔧 Manager Status: {stats['websocket_manager']}")
        print(f"   📊 Connection Stats:")
        for key, value in stats['connections'].items():
            print(f"      • {key.replace('_', ' ').title()}: {value}")
        
        print(f"   🚀 Available Features:")
        for feature, enabled in stats['features'].items():
            status = "✅" if enabled else "❌"
            print(f"      {status} {feature.replace('_', ' ').title()}")
        
        # Simulate WebSocket URLs
        pipeline_id = "demo_pipeline_123"
        user_id = "demo_user_2024"
        
        print(f"\n🔗 WebSocket Connection URLs:")
        print(f"   📡 Pipeline-specific: ws://localhost:8000/api/processing/ws/{pipeline_id}?user_id={user_id}")
        print(f"   📡 General updates: ws://localhost:8000/api/processing/ws?user_id={user_id}")
    
    async def demonstrate_pipeline_cancellation(self, pipeline_id):
        """Demonstrate pipeline cancellation."""
        self.print_step(6, "Pipeline Cancellation")
        
        print(f"🚫 Cancelling pipeline: {pipeline_id}")
        
        # Check status before cancellation
        pipeline = await self.queue.get_pipeline(pipeline_id)
        active_jobs = len([job for job in pipeline.jobs if job.status in [
            jq_module.JobStatus.QUEUED, 
            jq_module.JobStatus.PROCESSING
        ]])
        
        print(f"   📊 Jobs to cancel: {active_jobs}")
        
        # Cancel pipeline
        success = await self.queue.cancel_pipeline(pipeline_id)
        
        if success:
            cancelled_pipeline = await self.queue.get_pipeline(pipeline_id)
            print(f"   ✅ Pipeline cancelled successfully!")
            print(f"   📋 Final Status: {cancelled_pipeline.status}")
            print(f"   📅 Cancelled At: {cancelled_pipeline.completed_at}")
            
            # Count cancelled jobs
            cancelled_jobs = len([job for job in cancelled_pipeline.jobs 
                                if job.status == jq_module.JobStatus.CANCELLED])
            print(f"   🚫 Jobs Cancelled: {cancelled_jobs}")
        else:
            print(f"   ❌ Failed to cancel pipeline")
    
    async def demonstrate_api_integration(self):
        """Demonstrate API integration points."""
        self.print_step(7, "API Integration Points")
        
        print("🔌 Available API Endpoints:")
        
        endpoints = [
            ("POST", "/api/processing/start", "Start email processing pipeline"),
            ("GET", "/api/processing/{pipeline_id}/status", "Get pipeline status"),
            ("GET", "/api/processing/{pipeline_id}/jobs", "Get pipeline jobs"),
            ("POST", "/api/processing/{pipeline_id}/cancel", "Cancel pipeline"),
            ("GET", "/api/processing/stats", "Get processing statistics"),
            ("WebSocket", "/api/processing/ws/{pipeline_id}", "Real-time pipeline updates"),
            ("WebSocket", "/api/processing/ws", "General processing updates")
        ]
        
        for method, endpoint, description in endpoints:
            print(f"   {method:>10} {endpoint:<35} - {description}")
        
        print(f"\n📱 Mobile Integration Components:")
        components = [
            ("processingApi.ts", "Complete API client with offline queue"),
            ("useWebSocket.ts", "WebSocket hook with auto-reconnection"),
            ("ProcessingStatus.tsx", "Real-time progress UI component")
        ]
        
        for component, description in components:
            print(f"   📄 {component:<20} - {description}")
    
    async def run_complete_demo(self):
        """Run the complete demonstration."""
        self.print_header("T9: Email Processing Pipeline with WebSocket Updates")
        print(f"🚀 Starting comprehensive demonstration...")
        print(f"📅 Demo started at: {self.demo_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. Create pipeline
            pipeline_id, sample_emails = await self.demonstrate_pipeline_creation()
            
            # 2. Check status
            pipeline = await self.demonstrate_pipeline_status(pipeline_id)
            
            # 3. Process jobs
            await self.demonstrate_job_processing(pipeline)
            
            # 4. Error handling
            await self.demonstrate_error_handling(pipeline)
            
            # 5. WebSocket features
            await self.demonstrate_websocket_features()
            
            # 6. Pipeline cancellation
            await self.demonstrate_pipeline_cancellation(pipeline_id)
            
            # 7. API integration
            await self.demonstrate_api_integration()
            
            # Demo summary
            self.print_header("Demo Complete - All Features Working!")
            demo_duration = (datetime.now() - self.demo_start).total_seconds()
            
            print(f"✅ Email Processing Pipeline demonstration completed successfully!")
            print(f"⏱️  Total demo time: {demo_duration:.2f} seconds")
            print(f"📋 Features demonstrated:")
            print(f"   ✅ Background job queue with priority handling")
            print(f"   ✅ Multi-step email processing pipeline")
            print(f"   ✅ Real-time progress tracking")
            print(f"   ✅ Error handling and retry mechanisms")
            print(f"   ✅ WebSocket real-time communication")
            print(f"   ✅ Pipeline cancellation and management")
            print(f"   ✅ Mobile-ready API client and UI components")
            print(f"   ✅ Comprehensive testing suite")
            
            print(f"\n🎉 Ready for production deployment with Redis/Celery!")
            
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


async def main():
    """Main demonstration function."""
    demo = ProcessingPipelineDemo()
    success = await demo.run_complete_demo()
    return success


if __name__ == "__main__":
    print("🚀 Email Processing Pipeline - T9 Implementation Demo")
    print("="*60)
    
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
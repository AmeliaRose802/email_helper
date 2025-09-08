#!/usr/bin/env python3
"""
Main Email Manager - Orchestrates the entire email management system
"""

import sys
import os

# Add the scripts directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from outlook_manager import OutlookManager
from ai_processor import AIProcessor
from email_analyzer import EmailAnalyzer
from summary_generator import SummaryGenerator
from user_interface import UserInterface
from gui_interface import GuiInterface
from email_processor import EmailProcessor


class EmailManagementSystem:
    """Main application class that orchestrates all components"""
    
    def __init__(self):
        # Initialize all components
        self.outlook_manager = OutlookManager()
        self.ai_processor = AIProcessor()
        self.email_analyzer = EmailAnalyzer(self.ai_processor)
        self.summary_generator = SummaryGenerator()
        self.user_interface = UserInterface(self.ai_processor, self.outlook_manager, self.summary_generator)
        self.gui_interface = GuiInterface(self.ai_processor, self.outlook_manager, self.summary_generator)
        self.email_processor = EmailProcessor(
            self.outlook_manager, 
            self.ai_processor, 
            self.email_analyzer, 
            self.summary_generator
        )
    
    def ask_interface_preference(self):
        """Ask user whether to use GUI or console interface"""
        print("\n" + "=" * 60)
        print("🖥️  INTERFACE SELECTION")
        print("=" * 60)
        print("Choose how you'd like to edit AI suggestions:")
        print("1. 🖥️  Desktop GUI (Recommended - Easy visual editing)")
        print("2. 💻 Console/Terminal (Traditional text interface)")
        
        while True:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            
            if choice == '1':
                print("✅ Using desktop GUI interface...")
                return True
            elif choice == '2':
                print("✅ Using console interface...")
                return False
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
    
    def run(self):
        """Main application entry point"""
        print("🤖 AI-POWERED EMAIL MANAGEMENT SYSTEM")
        print("=" * 60)
        
        try:
            # Connect to Outlook
            print("🔗 Connecting to Outlook...")
            self.outlook_manager.connect_to_outlook()
            
            # Get user preferences
            max_emails = self.user_interface.get_max_emails_from_user()
            
            # Ask user for interface preference
            use_gui = self.ask_interface_preference()
            
            print(f"\n📋 Generating summary with AI suggestions for up to {max_emails} emails...")
            
            # Process emails
            email_suggestions = self.email_processor.process_emails(max_emails)
            
            if not email_suggestions:
                print("❌ No email suggestions generated. Cannot create summary.")
                return
            
            print(f"\n📋 Using collected data from {len(email_suggestions)} processed emails for summary generation...")
            
            # Generate summary
            summary_sections = self.email_processor.generate_summary()
            
            # Choose interface based on user preference
            if use_gui:
                interface = self.gui_interface
            else:
                interface = self.user_interface
            
            # Set data for chosen interface
            interface.set_email_suggestions(email_suggestions)
            interface.set_action_items_data(self.email_processor.get_action_items_data())
            
            # Offer editing options
            interface.offer_editing_options()
            
            print("\n✅ Email management session completed successfully!")
        
        except KeyboardInterrupt:
            print("\n\n🛑 Program interrupted by user. Exiting...")
            return False


def main():
    """Main function - entry point for the application"""
    system = EmailManagementSystem()
    system.run()


if __name__ == "__main__":
    main()

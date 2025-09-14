from twilio.rest import Client
from typing import List, Optional
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TwilioNotificationService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_phone = os.getenv("TWILIO_PHONE_NUMBER")
        self.to_phone = os.getenv("NOTIFICATION_PHONE_NUMBER")
        
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")

    def is_available(self) -> bool:
        """Check if Twilio integration is available"""
        return (self.client is not None and 
                self.from_phone is not None and 
                self.to_phone is not None)

    def send_sms(self, message: str, to_phone: str = None) -> Optional[str]:
        """Send SMS message"""
        if not self.is_available():
            logger.warning("Twilio integration not available")
            return None

        to_phone = to_phone or self.to_phone
        if not to_phone:
            logger.error("No destination phone number configured")
            return None

        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            logger.info(f"SMS sent successfully: {message_obj.sid}")
            return message_obj.sid
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return None

    def send_daily_schedule_reminder(self, schedule_items: List[dict], date: str) -> Optional[str]:
        """Send daily schedule reminder"""
        if not schedule_items:
            message = f"📅 FocusFlow Schedule for {date}\n\nNo tasks scheduled for today. Great job staying on top of things! 🎉"
        else:
            message = f"📅 FocusFlow Schedule for {date}\n\n"
            total_duration = 0
            
            for i, item in enumerate(schedule_items, 1):
                start_time = item['scheduled_start']
                end_time = item['scheduled_end']
                task_title = item['task_title']
                
                # Calculate duration
                start_minutes = self._time_to_minutes(start_time)
                end_minutes = self._time_to_minutes(end_time)
                duration = end_minutes - start_minutes
                total_duration += duration
                
                message += f"{i}. {start_time}-{end_time}: {task_title}\n"
            
            message += f"\n⏰ Total scheduled: {total_duration} minutes"
            message += f"\n💪 Stay focused and have a productive day!"

        return self.send_sms(message)

    def send_task_reminder(self, task_title: str, start_time: str, duration: int) -> Optional[str]:
        """Send task start reminder"""
        message = f"🚀 Task Starting Soon!\n\n📋 {task_title}\n⏰ {start_time}\n⏱️ Duration: {duration} minutes\n\nTime to focus! 💪"
        return self.send_sms(message)

    def send_break_reminder(self, break_duration: int) -> Optional[str]:
        """Send break reminder"""
        message = f"☕ Break Time!\n\nTake a {break_duration}-minute break to recharge.\n\n💡 Tip: Step away from your screen, stretch, or take a short walk.\n\nYou've got this! 🌟"
        return self.send_sms(message)

    def send_completion_celebration(self, completed_tasks: int, total_duration: int) -> Optional[str]:
        """Send task completion celebration"""
        message = f"🎉 Daily Goals Achieved!\n\n✅ Completed: {completed_tasks} tasks\n⏰ Total time: {total_duration} minutes\n\nAwesome work today! Your productivity is inspiring! 🌟"
        return self.send_sms(message)

    def send_motivational_message(self, tasks_remaining: int) -> Optional[str]:
        """Send motivational message for ongoing work"""
        messages = [
            f"🚀 Keep going! {tasks_remaining} tasks left to conquer today!",
            f"💪 You're doing great! Only {tasks_remaining} more tasks to go!",
            f"🌟 Stay focused! {tasks_remaining} tasks remaining - you've got this!",
            f"⚡ Momentum building! {tasks_remaining} tasks left on your journey to success!"
        ]
        
        # Simple rotation based on current hour
        current_hour = datetime.now().hour
        message = messages[current_hour % len(messages)]
        
        return self.send_sms(message)

    def send_energy_management_tip(self, energy_level: str) -> Optional[str]:
        """Send energy management tips based on current energy level"""
        if energy_level == "low":
            message = "🔋 Energy Running Low?\n\nTry these quick boosters:\n• Take 5 deep breaths\n• Drink some water\n• Do light stretching\n• Take a short walk\n\nSmall breaks lead to big gains! 💪"
        elif energy_level == "medium":
            message = "⚡ Steady Energy Detected!\n\nPerfect time for:\n• Focused work sessions\n• Tackling medium-priority tasks\n• Planning ahead\n\nYou're in the zone! Keep it up! 🎯"
        else:  # high energy
            message = "🚀 High Energy Alert!\n\nPerfect time for:\n• Challenging tasks\n• Creative work\n• Problem-solving\n• Learning new skills\n\nSeize this peak moment! 🌟"
        
        return self.send_sms(message)

    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight"""
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    def send_weekly_summary(self, total_tasks: int, total_hours: float, productivity_score: float) -> Optional[str]:
        """Send weekly productivity summary"""
        score_emoji = "🌟" if productivity_score >= 8 else "⚡" if productivity_score >= 6 else "💪"
        
        message = f"📊 Weekly FocusFlow Summary\n\n"
        message += f"✅ Tasks completed: {total_tasks}\n"
        message += f"⏰ Time invested: {total_hours:.1f} hours\n"
        message += f"📈 Productivity score: {productivity_score:.1f}/10 {score_emoji}\n\n"
        
        if productivity_score >= 8:
            message += "Outstanding week! You're a productivity champion! 🏆"
        elif productivity_score >= 6:
            message += "Great week! Your consistency is paying off! 🎯"
        else:
            message += "Every step counts! Next week is a fresh start! 🌱"
        
        return self.send_sms(message)
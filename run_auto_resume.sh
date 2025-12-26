#!/bin/bash
cd /opt/masterfilter
source venv/bin/activate
python manage.py auto_resume_jobs >> /var/log/masterfilter/auto_resume.log 2>&1

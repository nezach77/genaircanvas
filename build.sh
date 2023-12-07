aws ecr get-login-password --region us-east-1 | finch login --username AWS --password-stdin 063324463787.dkr.ecr.us-east-1.amazonaws.com
finch build -t airquality-demo .
finch tag airquality-demo 063324463787.dkr.ecr.us-east-1.amazonaws.com/airquality-demo:latest
finch push 063324463787.dkr.ecr.us-east-1.amazonaws.com/airquality-demo:latest
aws ecs update-service --cluster airquality-demo --service airquality-demo-app --force-new-deployment
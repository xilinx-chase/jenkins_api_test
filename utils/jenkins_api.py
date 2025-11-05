import argparse
import logging
import time

import jenkins

logger = logging.getLogger(__name__)


JENKINS_URL = "http://xsjvitisaijenkins:8080"

class JenkinsUtil:
    def __init__(self, url):
        self.server = jenkins.Jenkins(url)
        self.url = url
        logger.info(f"Initialized Jenkins connection to {url}")

    def build_job(self, job_name, parameters=None):
        if not self.server.job_exists(job_name):
            raise ValueError(f"Job {job_name} does not exist")
        if parameters:
            logger.info(f"Building {job_name} with parameters: {parameters}")
            queue_id = self.server.build_job(job_name, parameters)
        else:
            logger.info(f"Building {job_name} without parameters")
            queue_id = self.server.build_job(job_name)
        # 等待队列分配构建号
        build_info = self.server.get_queue_item(queue_id)
        attempts = 0
        max_attempts = 10
        while 'executable' not in build_info or not build_info.get('executable'):
            if attempts >= max_attempts:
                raise ValueError(f"Failed to get build number after {max_attempts} attempts")
            time.sleep(1)  # 等待 1 秒
            build_info = self.server.get_queue_item(queue_id)
            attempts += 1
        build_number = build_info['executable']['number']
        logger.info(f"Build number assigned: {build_number}")
        return build_number

    def get_job_info(self, job_name):
        try:
            return self.server.get_job_info(job_name)
        except Exception as e:
            logger.error(f"Failed to get info for job {job_name}: {str(e)}")
            raise

def get_jenkins():
    return JenkinsUtil(JENKINS_URL)

def test_build_trigger(request):
    # user_id = request.user_id
    job_name = request["job_name"]
    parameters = request["parameters"]

    client = get_jenkins()

    build_number = client.build_job(job_name, parameters)
    job_info = client.get_job_info(job_name)
    job_url = job_info["url"]
    build_url = f"{job_url}/{build_number}"
    logger.info(f"Build triggered for {job_name}, build number: {build_number}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Jenkins trigger LLM CI")
    parser.add_argument('--job', type=str, default="", help="Jenkins job name")
    parser.add_argument('--model_path', type=str, default="", help="Model path parameter for the job")
    args = parser.parse_args()
    request = {
        "job_name": args.job,
        "parameters": {"MODEL_PATH": args.model_path, "EXECUTION_MODE": "analyze"}
    }
    test_build_trigger(request)

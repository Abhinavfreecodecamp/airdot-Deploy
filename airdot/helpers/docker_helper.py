import os
import string
import random
import docker
from airdot.helpers.template_helpers import get_docker_template

DEFAULT_PKG_LIST = ['Flask', 'gunicorn']

class docker_helper:
    def __init__(self):
        self.client = docker.from_env()
    
    def run_container(self, image_name, command=None, detach=True, remove=True, ports=None):
        try:
            container = self.client.containers.run(image_name, command, detach=detach, remove=remove, ports=ports)
            return container
        except docker.errors.ImageNotFound:
            print(f"Error: Image '{image_name}' not found")
        except docker.errors.APIError as e:
            print(f"Error starting container: {e}")

    def get_container_id(self, image_name):
        try:
            container = self.client.containers.get(image_name)
            return container.id
        except docker.errors.NotFound:
            print(f"Error: Container '{image_name}' not found")
        except docker.errors.APIError as e:
            print(f"Error getting container ID: {e}")
    
    def kill_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.kill()
            return True
        except docker.errors.NotFound:
            print(f"Error: Container '{container_id}' not found")
        except docker.errors.APIError as e:
            print(f"Error killing container: {e}")
            return False
    
    def delete_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.remove()
            return True
        except docker.errors.NotFound:
            print(f"Error: Container '{container_id}' not found")
        except docker.errors.APIError as e:
            print(f"Error deleting container: {e}")
            return False
        
    def restart_container(self, container_id):
        try:
            container = self.client.containers.get(container_id)
            container.restart()
            print(f"Container '{container_id}' restarted successfully")
        except docker.errors.NotFound:
            print(f"Container '{container_id}' not found")

    def create_docker_runtime(self, deploy_dict):
        dir = self.write_user_file(deploy_dict['sourceFile'])
        custum_req = self.get_custom_requirements(deploy_dict['requirementsTxt'])
        success_flag = self.create_custom_docker_file(custum_req, dir)
        print('flag 1')
        if success_flag:
            image, _ = self.client.images.build(path=f'/tmp/{dir}/', tag=f"{deploy_dict['name']}")
            print('flag 2')
            return image, dir
        return None, None

    def create_custom_docker_file(self, custum_req, dir):
        try:
            docker_template = get_docker_template(custum_req)
            with open(f'/tmp/{dir}/Dockerfile', 'w') as py_file:
                py_file.write('\n'.join(docker_template) + '\n')
            return True
        except:
            return False

    def get_custom_requirements(self, requirementsTxt):
        pkg_list = requirementsTxt.split('\n')
        return " ".join(pkg_list + DEFAULT_PKG_LIST ) 

    def write_user_file(self, sourceFile):
        try:
            dir = self.id_generator()
            os.mkdir(f'/tmp/{dir}')
            with open(f'/tmp/{dir}/app.py', 'w') as py_file:
                py_file.write('\n'.join(sourceFile['contents'].split('\n')) + '\n')
            return dir
        except:
            return None

    def id_generator(self, size=4, chars=string.ascii_lowercase + string.digits):
        return "".join(random.choice(chars) for _ in range(size))
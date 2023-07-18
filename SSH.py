import paramiko
import json
import os


class SSHManager:
    def __init__(self):
        self.config_file = "config.json"
        self.config_data = self.load_config()

    def save_config(self):
        with open(self.config_file, "w") as config_file:
            json.dump(self.config_data, config_file, indent=4)

    def load_config(self):
        config_data = {}
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as config_file:
                try:
                    config_data = json.load(config_file)
                except json.JSONDecodeError:
                    pass
        return config_data

    def add_ssh_connection(self, host_ip, host_password=None):
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # 连接服务器
            if host_password:
                ssh.connect(hostname=host_ip, port=22, username='root', password=host_password)
            else:
                # 使用密钥认证
                private_key_file = f"{host_ip}_private.key"
                if os.path.exists(private_key_file):
                    private_key = paramiko.RSAKey(filename=private_key_file)
                    ssh.connect(hostname=host_ip, port=22, username='root', pkey=private_key)
                else:
                    print(f"未找到密钥文件 {private_key_file}，请确保已经生成密钥对。")
                    return None

            return ssh

        except paramiko.AuthenticationException:
            print("认证失败，请检查主机IP和密码是否正确。")
        except paramiko.SSHException as e:
            print(f"SSH连接错误: {e}")

        return None

    def generate_key_pair(self, host_ip):
        private_key_file = f"{host_ip}_private.key"
        public_key_file = f"{host_ip}_public.key"
        if not os.path.exists(private_key_file) and not os.path.exists(public_key_file):
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(private_key_file)
            with open(public_key_file, "w") as public_key:
                public_key.write(f"{key.get_name()} {key.get_base64()}")

            print(f"已生成密钥对：\n私钥保存至 {private_key_file}\n公钥保存至 {public_key_file}")
        else:
            print("密钥对已存在，无需重新生成。")

    def run_ssh_commands(self, ssh):
        print("请输入要执行的命令 \n"
                            "(输入'exit'退出 \n使用fdownload来下载指定的文件EX:fdownload /root/config.json config.json\n"
                            ",使用fput来上传指定的文件到服务器中 EX:fput config.json /root/config.json): \n")
        while True:
            command = input("请输入要执行的命令: \n")
            if command.lower() == "exit":
                break
            elif command.lower().startswith("fdownload "):
                try:
                   _, remote_file, local_file = command.split(" ")
                except:
                    print("确保参数正确!")
                self.ftp_download(ssh, remote_file, local_file)
            elif command.lower().startswith("fput "):
                try:
                   _, local_file, remote_file = command.split(" ")
                except:
                    print("确保参数正确!")
                self.ftp_upload(ssh, local_file, remote_file)
            else:
                # 执行命令
                stdin, stdout, stderr = ssh.exec_command(command)
                # 获取命令结果
                res, err = stdout.read(), stderr.read()
                result = res if res else err
                print(result.decode())


    def ftp_download(self, ssh, remote_file, local_file):
        try:
            sftp = ssh.open_sftp()
            sftp.get(remote_file, local_file)
            print(f"成功下载文件：{remote_file} 到本地：{local_file}")
            sftp.close()
        except FileNotFoundError:
            print(f"服务器上找不到文件：{remote_file}")
        except Exception as e:
            print(f"下载文件出错：{e}")

    def ftp_upload(self, ssh, local_file, remote_file):
        try:
            sftp = ssh.open_sftp()
            sftp.put(local_file, remote_file)
            print(f"成功上传文件：{local_file} 到服务器：{remote_file}")
            sftp.close()
        except FileNotFoundError:
            print(f"本地找不到文件：{local_file}")
        except Exception as e:
            print(f"上传文件出错：{e}")


    def main(self):
        for host_ip, host_password in self.config_data.items():
            ssh = self.add_ssh_connection(host_ip, host_password)
            if ssh:
                print(f"连接到主机 {host_ip}")
                self.run_ssh_commands(ssh)
                ssh.close()

        add_new_host = input("是否添加新的主机连接？(yes/no): ")
        if add_new_host.lower() == "yes":
            host_ip = input("请输入主机IP地址: ")
            generate_key_pair = input("是否生成密钥对？(yes/no): ")

            if generate_key_pair.lower() == "yes":
                self.generate_key_pair(host_ip)
            else:
                host_password = input("请输入主机密码: ")
                ssh = self.add_ssh_connection(host_ip, host_password)
                if ssh:
                    print(f"连接到新主机 {host_ip}")
                    self.run_ssh_commands(ssh)
                    ssh.close()


if __name__ == "__main__":
    ssh_manager = SSHManager()
    ssh_manager.main()

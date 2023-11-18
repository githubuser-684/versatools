from Tool import Tool
import os
from utils import Utils
import httpx
import random
import subprocess
import urllib.parse
import concurrent.futures
import win32event
import threading
import psutil
import eel


class GameVisits(Tool):
    def __init__(self, app):
        super().__init__("Game Visits", "Boost game visits", 2, app)

    @Tool.handle_exit
    def run(self):
        max_generations = self.config["max_generations"]
        timeout = self.config["timeout"]
        place_id = self.config["place_id"]
        max_workers = self.config["max_workers"]

        eel.write_terminal("\x1B[1;33mWarning: on Windows 11, it may not be possible to run multiple roblox instances\x1B[0;0m")

        self.roblox_player_path = self.find_roblox_player()

        if max_workers == None or max_workers > 1:
            # remove singleton mutex
            threading.Thread(target=self.remove_singleton_mutex).start()

        req_sent = 0
        req_failed = 0
        total_req = max_generations

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as self.executor:
            results = [self.executor.submit(self.visit_game, self.get_random_cookie(), place_id, timeout) for i in range(max_generations)]

            for future in concurrent.futures.as_completed(results):
                try:
                    is_success, response_text = future.result()
                except Exception as e:
                    is_success, response_text = False, str(e)

                if is_success:
                    req_sent += 1
                else:
                    req_failed += 1

                self.print_status(req_sent, req_failed, total_req, response_text, is_success, "New visits")

    @Utils.handle_exception()
    def visit_game(self, cookie, place_id, timeout):
        csrf_token = self.get_csrf_token(cookie)
        user_agent = self.get_random_user_agent()

        auth_ticket = self.get_auth_ticket(cookie, user_agent, csrf_token)
        self.open_instance(auth_ticket, place_id, timeout)
        return True, "Cookie visited the game"

    def get_auth_ticket(self, cookie, user_agent, csrf_token):
        headers = self.get_roblox_headers(user_agent, csrf_token)

        cookies = { ".ROBLOSECURITY": cookie }

        response = httpx.post("https://auth.roblox.com/v1/authentication-ticket/", headers=headers, cookies=cookies)
        try:
            return response.headers["rbx-authentication-ticket"]
        except Exception:
            raise Exception("Rbx-auth-ticket not found. " + Utils.return_res(response))

    def kill(self, proc_pid):
        process = psutil.Process(proc_pid)
        for proc in process.children(recursive=True):
            proc.kill()
        process.kill()

    def open_instance(self, auth_ticket, place_id, timeout):
        cmd = self.get_rbx_cmd(auth_ticket, place_id)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            if stderr:
               raise Exception("Failed to communicate with instance. " + str(stderr))
        except subprocess.TimeoutExpired:
            self.kill(proc.pid)

    def get_rbx_cmd(self, auth_ticket, place_id):
        browser_tracker_id = random.randint(200000000000, 210000000000)
        join_attempt_id = ""

        launcherurl = f'https://assetgame.roblox.com/game/PlaceLauncher.ashx?request=RequestGame&browserTrackerId={browser_tracker_id}&placeId={place_id}&isPlayTogetherGame=false&joinAttemptId={join_attempt_id}&joinAttemptOrigin=PlayButton'

        return f'"{self.roblox_player_path}" roblox-player:1+launchmode:play+gameinfo:{auth_ticket}+'\
            f'launchtime:{Utils.utc_sec()}+placelauncherurl:{urllib.parse.quote(launcherurl)}'\
                f'+browsertrackerid:{browser_tracker_id}+robloxLocale:en_en+gameLocale:en_en+channel:+LaunchExp:InApp'

    def find_roblox_player(self):
        user_home = os.path.expanduser("~")
        program_files_x86 = os.environ.get("ProgramFiles(x86)")

        base_directories = [
            os.path.join(user_home, "AppData", "Local", "Roblox", "Versions"),
            os.path.join(program_files_x86, "Roblox", "Versions"),
        ]

        for base_directory in base_directories:
            for root, dirs, files in os.walk(base_directory):
                if "RobloxPlayerBeta.exe" in files:
                    return os.path.join(root, "RobloxPlayerBeta.exe")

        raise FileNotFoundError("Could not find path to Roblox executable")

    def remove_singleton_mutex(self):
        while True:
            win32event.CreateMutex(None, 1, "ROBLOX_singletonMutex")

            if self.exit_flag is False:
                break
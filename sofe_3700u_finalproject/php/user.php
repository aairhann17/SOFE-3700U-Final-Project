<?php
	class Users {
		public function __construct(protected PDO $database){}
		
		public function createUser(string $email, string $username, string $user_password, int $role) {
			$password_hash = password_hash($user_password, PASSWORD_DEFAULT); //hash password
			
			$stmt = $this->database->prepare("SELECT ID FROM user WHERE email = :email"); //check if email is already in database
			$stmt->execute(['email' => $email]);
			$result = $stmt->fetchAll();
			if (count($result) > 0) { //if so, return 1
				return 1;
			}
			
			$stmt = $this->database->prepare("SELECT ID FROM user WHERE username = :username"); //check if username is already in database
			$stmt->execute(['username' => $username]);
			$result = $stmt->fetchAll();
			if (count($result) > 0) { //if so, return 2
				return 2;
			}
			
			try { //create user
				$stmt = $this->database->prepare("INSERT INTO user (email, username, user_password, role)
										VALUES (:email, :username, :user_password, :role)");
				$stmt->execute(['email' => $email, 'username' => $username, 'user_password' => $password_hash, 'role' => $role]);
				return 0; //return 0 if successful
								
			} catch (PDOException $e) {
				error_log($e->getMessage());
				echo $e; //remove once ready to submit
				return 3;
			}
		}
		
		public function authenticate(string $username, string $password) {
			try {
				$stmt = $this->database->prepare("SELECT ID, user_password FROM user WHERE username = :username");
				$stmt->execute([":username" => $username, ]);
			} catch (PDOException $e) {
					error_log($e->getMessage());
					echo $e; //remove once ready to submit
					return false;
			}
		
			$user = $stmt->fetch(PDO::FETCH_ASSOC);
			
			if (!$user) {
				return false;
			}
			
			$auth = password_verify($password, $user["user_password"]);
			
			if ($auth) {
				return intval($user["ID"]);
			}
			
			return false;
		}
		
		public function signin(int $userID) {
			if (session_status() === PHP_SESSION_NONE) {
				return false;	
			}
			$_SESSION["loggedInUser"] = $userID;
		}
		
		public function getLoggedInUser() {
			if (session_status() === PHP_SESSION_NONE) {
				return false;	
			}
			
			if (!isset($_SESSION["loggedInUser"])) {
				return false;
			}
			
			return intval($_SESSION["loggedInUser"]);
		}
		
		public function logout() {
			session_regenerate_id(true);
			$_SESSION["loggedInUser"] = null;
		}
	}
?>

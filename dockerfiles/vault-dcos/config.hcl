listener "tcp" {
  address = "0.0.0.0:8200"
  tls_cert_file = "/tmp/server-cert.pem"
  tls_key_file = "/tmp/server-key.pem"
}

backend "zookeeper" {
  address = "master.mesos:2181"
  path = "vault"
  advertise_addr = "https://vault.marathon.mesos:8200"
}

disable_mlock = true

#!/bin/bash

set -euo pipefail
trap 'echo "An error occurred. Exiting..."; exit 1' ERR

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then 
  echo "Switching to root..."
  exec sudo bash "$0" "$@"
fi

# Variables
VPN_SUBNET="172.16.0.0/24"
EXT_IFACE="eth0"  # Change if needed
CLIENT_NAME="client1"
OVPN_DIR="/home/ec2-user/openvpn-client-files"
CLIENT_CONFIG="$OVPN_DIR/$CLIENT_NAME.ovpn"
EASYRSA_DIR="/etc/openvpn/easy-rsa"
PKI_DIR="$EASYRSA_DIR/easyrsa/pki"
SERVER_CONF="/etc/openvpn/server/server.conf"
LOG_FILE="/var/log/openvpn.log"
STATUS_LOG="/var/log/openvpn-status.log"

# Function to install a package if not already installed
install_package() {
    if ! rpm -q "$1" &>/dev/null; then
        echo "Installing $1..."
        yum install -y "$1"
    else
        echo "$1 is already installed."
    fi
}

# Function to get server's public IP address
get_server_ip() {
    local SERVER_IP
    SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || true)

    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(curl -s https://ifconfig.me || true)
    fi

    if [ -z "$SERVER_IP" ]; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
    fi

    echo "$SERVER_IP"
}

# Function to update and upgrade system
update_system() {
    echo "Updating system..."
    yum update -y
    sleep 1
}

# Function to install required packages
install_packages() {
    install_package "openvpn"
    sleep 1
    echo "Installing easy-rsa manually..."
    yum install -y git
    if [ -d "$EASYRSA_DIR" ]; then
        echo "Deleting existing Easy-RSA directory..."
        rm -rf "$EASYRSA_DIR"
    fi
    git clone https://github.com/OpenVPN/easy-rsa.git "$EASYRSA_DIR"
    cd "$EASYRSA_DIR"
    mkdir -p "$PKI_DIR"
    cd "$EASYRSA_DIR"
    ./easyrsa init-pki
    sleep 1
}

# Function to create Certificate Authority (CA)
create_ca() {
    cd "$EASYRSA_DIR"

    if [ -d "$PKI_DIR" ]; then
        echo "Deleting existing PKI directory..."
        rm -rf "$PKI_DIR"
        sleep 1
    fi

    echo "Initializing PKI..."
    ./easyrsa init-pki
    sleep 1

    echo "Building CA..."
    ./easyrsa --batch build-ca nopass
    sleep 1

    if [ ! -f "$EASYRSA_DIR/pki/ca.crt" ]; then
        echo "Error: Failed to create CA certificate. Exiting..."
        exit 1
    fi
}

# Function to generate server certificate and key
generate_server_cert() {
    echo "Generating server certificate and key..."
    cd "$EASYRSA_DIR"
    ./easyrsa --batch gen-req server nopass
    ./easyrsa --batch sign-req server server
    sleep 1

    if [ ! -f "$EASYRSA_DIR/pki/issued/server.crt" ] || [ ! -f "$EASYRSA_DIR/pki/private/server.key" ]; then
        echo "Error: Failed to generate server certificate or key. Exiting..."
        exit 1
    fi
}

# Function to generate Diffie-Hellman parameters
generate_dh_params() {
    if [ ! -f "$EASYRSA_DIR/pki/dh.pem" ]; then
        echo "Generating Diffie-Hellman parameters..."
        cd "$EASYRSA_DIR"
        ./easyrsa gen-dh
        sleep 1
        if [ ! -f "$EASYRSA_DIR/pki/dh.pem" ]; then
            echo "Error: Failed to generate Diffie-Hellman parameters. Exiting..."
            exit 1
        fi
    else
        echo "Diffie-Hellman parameters already exist."
    fi
}

# Function to generate TLS-Auth key
generate_tls_auth_key() {
    if [ ! -f "/etc/openvpn/ta.key" ]; then
        echo "Generating TLS-Auth key..."
        openvpn --genkey --secret /etc/openvpn/ta.key
        sleep 1
        if [ ! -f "/etc/openvpn/ta.key" ]; then
            echo "Error: Failed to generate TLS-Auth key. Exiting..."
            exit 1
        fi
    else
        echo "TLS-Auth key already exists."
    fi
}

# Function to enable IP forwarding
enable_ip_forwarding() {
    echo "Enabling IP forwarding..."
    grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf || echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
    sysctl -p
    sleep 1
}

# Function to create log files for OpenVPN
create_log_files() {
    for file in "$LOG_FILE" "$STATUS_LOG"; do
        if [ ! -f "$file" ]; then
            echo "Creating log file $file..."
            touch "$file"
            chmod 644 "$file"
            sleep 1
        fi
    done
}

# Function to create server.conf for OpenVPN
create_server_conf() {
    if [ -f "$SERVER_CONF" ]; then
        echo "Deleting old server.conf..."
        rm -f "$SERVER_CONF"
        sleep 1
    fi

    echo "Creating OpenVPN server configuration file..."
    cat <<EOF > "$SERVER_CONF"
port 1194
proto udp4
dev tun
ca $EASYRSA_DIR/pki/ca.crt
cert $EASYRSA_DIR/pki/issued/server.crt
key $EASYRSA_DIR/pki/private/server.key
dh $EASYRSA_DIR/pki/dh.pem
tls-auth /etc/openvpn/ta.key
server 172.16.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
keepalive 10 120
topology subnet
auth SHA256
persist-key
persist-tun
status $STATUS_LOG
log $LOG_FILE
verb 3
explicit-exit-notify 1
data-ciphers AES-256-GCM:AES-128-GCM:AES-256-CBC
EOF
    sleep 1
}

# Function to restart OpenVPN service
restart_openvpn_service() {
    if systemctl is-active --quiet openvpn-server@server.service; then
        echo "Stopping OpenVPN service..."
        systemctl stop openvpn-server@server.service
        sleep 1
    fi

    systemctl daemon-reload
    echo "Reloading OpenVPN service with new settings..."
    systemctl start openvpn-server@server
    systemctl enable openvpn-server@server
    sleep 1
}

# Function to set up client configuration directory
setup_client_config_directory() {
    if [ -d "$OVPN_DIR" ]; then
        echo "Deleting existing client configuration directory..."
        rm -rf "$OVPN_DIR"
        sleep 1
    fi
    mkdir -p "$OVPN_DIR"
    chmod 777 "$OVPN_DIR"
    sleep 1
}

# Function to copy necessary files for client
copy_client_files() {
    echo "Copying necessary files to $OVPN_DIR..."
    for file in "$PKI_DIR/issued/$CLIENT_NAME.crt" "$PKI_DIR/private/$CLIENT_NAME.key" "$PKI_DIR/ca.crt" "/etc/openvpn/ta.key"; do
        if [ -f "$file" ]; then
            cp "$file" "$OVPN_DIR/"
            chmod 777 "$OVPN_DIR/$(basename "$file")"
            sleep 1
        else
            echo "Error: Required file $file not found. Exiting..."
            exit 1
        fi
    done
}

# Function to create the .ovpn client configuration file
create_client_ovpn() {
    if [ -f "$CLIENT_CONFIG" ]; then
        echo "Deleting old $CLIENT_NAME.ovpn file..."
        rm -f "$CLIENT_CONFIG"
        sleep 1
    fi

    SERVER_IP=$(get_server_ip)
    if [ -z "$SERVER_IP" ]; then
        echo "Error: Could not determine server IP address. Exiting..."
        exit 1
    fi

    echo "Creating $CLIENT_NAME.ovpn file with dynamic server IP ($SERVER_IP)..."
    cat <<EOF > "$CLIENT_CONFIG"
client
dev tun
proto udp4
remote $SERVER_IP 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
tls-auth ta.key
data-ciphers AES-256-GCM:AES-128-GCM
cipher AES-256-CBC
verb 3
key-direction 1

<ca>
$(cat "$OVPN_DIR/ca.crt")
</ca>

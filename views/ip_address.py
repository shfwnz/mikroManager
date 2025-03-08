import streamlit as st
import time

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

def get_interface(client):
    output, _ = execute_command(client, "/interface print terse")
    
    interfaces = []
    for line in output.split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            interfaces.append(parts[2].replace("name=", ""))
            
    return interfaces

def rerun_after(timer):
    time.sleep(timer)
    st.rerun()

def subnet_mask_to_cidr(subnet_mask):
    return sum(bin(int(x)).count('1') for x in subnet_mask.split('.'))

def delete_ip(client, index, address):
    st.write(f"Deleting IP address with index: {index}") 
    _, error = execute_command(client, f"/ip address remove numbers={index}")
    
    if error:
        st.error(f"Failed to delete {address}: {error}")
    else:
        st.success(f"Deleted IP {address}")
        rerun_after(3)
        
def get_ip(output):    
    col_headers = st.columns([3,2,1.5,1,1])
    with col_headers[0]: st.markdown("**Address**")
    with col_headers[1]: st.markdown("**Network**")
    with col_headers[2]: st.markdown("**Interface**")
    with col_headers[3]: st.markdown("**Status**")
    with col_headers[4]: st.markdown("**Action**")
    
    found_ips = False
    for line in output.split("\n"):
        if not line.strip():
            continue
            
        found_ips = True
        parts = line.split()
        if len(parts) >= 4:
            index = parts[0].split('=')[-1]  
            
            address = parts[1].split('=')[-1]
            network = parts[2].split('=')[-1]
            interface = parts[3].split('=')[-1]
            status_code = ""
            
            status_text = {
                "": "Active",
                "D": "Dynamic",
                "X": "Disabled",
                "I": "Invalid"
            }.get(status_code, "Unknown")
            
            cols = st.columns([3,2,1.5,1,1])
            with cols[0]: st.write(address)
            with cols[1]: st.write(network)
            with cols[2]: st.write(interface)
            with cols[3]: st.write(status_text)
            with cols[4]:
                if st.button("Delete", key=f"del_{index}", use_container_width=True):
                    delete_ip(client, index, address)
    
    if not found_ips:
        st.info("No IP addresses found")

def show_ip(client):
    st.subheader("IP Addresses")
    output, _ = execute_command(client, "/ip address print terse")
    get_ip(output)
    
def ip_conf(client):
    interfaces = get_interface(client)
    
    if not interfaces:
        st.warning("Interfaces not found")
        return
            
    selected_interface = st.selectbox("Select Interface:", interfaces, placeholder="choose an interfaces", index=None)
    
    message_success = ""
    message_error = ""
    
    col1, spacer, col2 = st.columns([1,2,1])
    with col1:
        if st.button("Enable Interface", use_container_width=True):
            enable_command = f"/interface enable {selected_interface}"
            stdin, stdout, stderr = client.exec_command(enable_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            if error:
                message_error = f"Unable to enable {selected_interface}: {error}"
            else:
                message_success = f"Enabled {selected_interface}"
    with col2:
        if st.button("Disable Interface", use_container_width=True):
            disable_command = f"/interface disable {selected_interface}"
            stdin, stdout, stderr = client.exec_command(disable_command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            if error:
                message_error = f"Unable to disable {selected_interface}: {error}"
            else:
                message_success = f"Disabled {selected_interface}"
    
    if message_error:
        st.error(message_error)    
    elif message_success:
        st.success(message_success) 
    
    ip_address = st.text_input("IP Address:", placeholder="Enter the IP address of the device", help="Example: 192.168.88.1")
    subnet_mask = st.text_input("Subnet:", placeholder="Enter a subnet mask for the device", help="Example: 255.255.255.0")
    remove_old = st.checkbox("Remove old IP before applying", False)
    
    st.subheader("Apply Configuration")
    if st.button("Apply Configuration"):
        try:
            cidr = subnet_mask_to_cidr(subnet_mask)
            ip_with_subnet = f"{ip_address}/{cidr}"
            
            if remove_old:
                remove_command = f"/ip address remove [find interface={selected_interface}]"
                client.exec_command(remove_command)
                st.warning(f"Removing old IPs on {selected_interface}...")
            
            command = f"/ip address add address={ip_with_subnet} interface={selected_interface}"
            stdin, stdout, stderr = client.exec_command(command)
            stdout.channel.recv_exit_status()
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if error:
                st.error(f"Error: {error}")
            else:
                st.success(f"New IP {ip_with_subnet} applied to {selected_interface}")
                st.rerun()
            
        except Exception as e:
            st.error(f"Failed to Set IP: {e}")

if 'ssh_connection' not in st.session_state or not st.session_state['ssh_connection']:
    st.warning("Please connect to the Router first")
else:
    st.header("IP Address Configuration")
    tab1, tab2 = st.tabs(["Show IP", "Add IP"])
    try:
        client = st.session_state.get('ssh_client', None)
        if client is None:
            st.error("SSH client is not available. Please reconnect")
        else:
            with tab1:
                show_ip(client)
            with tab2:               
                ip_conf(client)
                
    except Exception as e:
        st.error(f"Failed: {e}")
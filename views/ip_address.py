import streamlit as st
import time

def subnet_mask_to_cidr(subnet_mask):
    return sum(bin(int(x)).count('1') for x in subnet_mask.split('.'))

if 'ssh_connection' not in st.session_state or not st.session_state['ssh_connection']:
    st.warning("Please connect to the Router first")
else: 
    st.header("IP Address Configuration")
    try:
        client = st.session_state.get('ssh_client', None)
        if client is None:
            st.error("SSH client is not available. Please reconnect")
        else:
            get_interface = f"/interface print terse"
            stdin, stdout, stderr = client.exec_command(get_interface)
            output = stdout.read().decode().strip()
            
            interfaces = []
            for line in output.split("\n"):
                parts = line.split()
                if len(parts) >= 3:  
                    interfaces.append(parts[2].replace("name=", "")) 
                    
            selected_interface = st.selectbox("Select Interface:", interfaces)
            
            ip_address = st.text_input("IP Address:", placeholder="Enter the IP address of the device", help="Example: 192.168.88.1")
            subnet_mask = st.text_input("Subnet:", placeholder="Enter a subnetmask for the device", help="Example: 255.255.255.0")
            remove_old = st.checkbox("Remove old IP before applying", False)
            
            st.subheader("Enable/Disable Interface")
            
            message_success = ""
            message_error = ""
            
            col1, col2 = st.columns([1,3])
            with col1:
                if st.button("Enable Interface"):
                    enable_command = f"/interface enable {selected_interface}"
                    stdin, stdout, stderr = client.exec_command(enable_command)
                    
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        message_error = f"Unable to enable {selected_interface}: {error}"
                    else:
                        message_success = f"Enabling {selected_interface}"
            with col2:
                if st.button("Disable Interface"):
                    disable_command = f"/interface disable {selected_interface}"
                    stdin, stdout, stderr = client.exec_command(disable_command)
                    
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        message_error = f"Unable to disabling {selected_interface}: {error}"
                    else:
                        message_success = f"Disabling {selected_interface}"
                        
            if message_error:
                with st.spinner():
                    time.sleep(2)
                    st.error(message_error)    
            else:
                with st.spinner():
                    time.sleep(2)
                    st.success(message_success) 
            
            st.subheader("Apply Configuration")
            if st.button("Apply Configuration"):
                try:
                    cidr = subnet_mask_to_cidr(subnet_mask)
                    ip_with_subnet = f"{ip_address}/{cidr}"
                    
                    if remove_old:
                        remove_command = f"/ip address remove [find interface={selected_interface}]"
                        client.exec_command(remove_command)
                        st.warning(f"Removing old IPs on {selected_interface}...")
                    
                    command = f"ip address add address={ip_with_subnet} interface={selected_interface}"
                    
                    stdin, stdout, stderr = client.exec_command(command)
                    
                    # st.write(f"Executing: `{command}`")
                    
                    stdout.channel.recv_exit_status()
                    output = stdout.read().decode().strip()
                    error = stderr.read().decode().strip()
                    
                    if error:
                        st.error(f"Error: {error}")
                    else:
                        st.success(f"New IP {ip_with_subnet} applied to {selected_interface}")
                    
                except Exception as e:
                    st.error(f"Failed to Set IP: {e}")
            
    except Exception as e:
        st.error(f"Failed: {e}")
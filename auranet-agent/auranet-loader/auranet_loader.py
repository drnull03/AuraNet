#!/usr/bin/env python3
import time
import libbpf


OBJECT_FILE = "../../eBPF/bpf/objs/bpf_generic_kprobe_v61.o"

def main():
    print(f"Opening eBPF object: {OBJECT_FILE}")
    
    try:
     
        obj = libbpf.BpfObject(OBJECT_FILE)
        
        # load into the kernel
        # this print will only work if connected to tty
        print("Loading programs into the kernel...")
        obj.load()

        # replaced for eBPF map purposes
        prog = obj.get_program("bpf_generic_kprobe") 
        

        # print will only work if terminal is present
        if not prog:
            print("Failed to find the specified program in the object file.")
            return

        # Attach the program to the kernel hook
        print("Attaching program...")
        link = prog.attach()

        print("Successfully attached! Waiting for events... (Ctrl+C to exit)")
        
        
        #will only work if terminal is connect    
    except KeyboardInterrupt:
        print("\nDetaching and exiting...")
    except Exception as e:
        print(f"\nError: {e}")
        print("Note: If the kernel rejected the program, it is likely because "
              "]-specific maps or tail calls were not initialized.")

if __name__ == "__main__":
    main()
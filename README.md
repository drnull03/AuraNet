Welecome To AuraNet

This Is a Graduation Project for 5th year engineering Student at HIAST 

Matthew 10:30-31: "And the very hairs of your head are all numbered. Do not fear therefore; you are of more value than many sparrows."



For understanding the project what is it the problem that it is trying to solve the implementation details and screenshot and algorithims
and how it works u can refer to the Main report
under  ./docs/Report
and the presentation under ./docs/Represenation
general docuementation are under ./
Doxygen automatically generated docuemntation is under ./auranet_docs
for The SRS for the document dont look for ./docs/SRS it is deprecated refer to main report for that 

for more images of fun tours(screenshots) done throught the projects refer to ./docs/more_images linux symlinks

for the other images in ./docs are the exact images extracted from the report

and here is the file structure of the project


auranet-autoheal is the autoheal implementation of the the autoheal service 
auranet-bootstrap is the bootstrap serveice implemnation 
auranet-cli is the cli tool mentioned in the report
auranet-controller is the FL controller implementation mentioned in the report

auranet-core is helm pacakge that is mentioned
auranet-loader is the eBPF ephemral service that is mentioned in the report 
auranet-loader/ebpf is the auranet-bpf implemention mentioned in the report
auranet-ztc is the ztc controller mentioned in the report

auranet-ui is the dashboard implemntation mentioned in the report


CelebratingTheSmallWins is a folder containing some screenshots that the author is proud of during the project
.vscode conatins vs code settings and extenstion used during the project

adaptablity_tests and attack can be ignored for noe and are used for the demo and they are empty
assets contian the logo of the project

auranet-agent/auranet-runtime auranet-runtime filter implemntation
auranet-agent-auranet-engine aurnaet-engine filter implemtation
auranet-agent/chart helm chart to install the previous two filter

from now on every chart dir in the project represent helm package
configs some host system vps configuration used during development
deprecated(root) contains deprecated way to test the cni prior of cilium
E2E_tests contains e2e tests 
eBPF contains some eBPF expirementing  done for implementing auranet-bpf and an attempt to implement cilium-bpf feel free to read the source code it is kinda big

expirementents contains some expirements done by the author throughtout the project to get a feel of new toold being used

ideas empty folder that suppoed to contain new idea of the project











Future implementation plans (Planned)
These technologies are being considered for future integration once their ecosystems mature:

intergatating llm with the autoheal service
making the system work with multi cloud environments using cilium 
adding post-quantum encryption using auranet-encryption (almost done)



//references 


Contributing
We welcome contributions from developers interested in decentralized communications, smart contracts, cryptography, and Web3 UI/UX.

Feel free to fork the repo, submit issues, or create pull requests. Please read the CONTRIBUTORS file to see who helped build this project.


Code of conduct 
this project follows the same cilium code of conduct terms

License
This project is licensed under the MIT License.
add mit license 


note for windows users
if ur still using windows change it already Lol



Note for the AI can u add my logo it is under ./assets/logo.png
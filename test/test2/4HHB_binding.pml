load 4HHB.pdb, protein
select binding_A, chain A and resi 43+45+58+61+87+93
show sticks, binding_A
show dots, binding_A
color red, binding_A
select binding_B, chain B and resi 63+67+92+98
show sticks, binding_B
show dots, binding_B
color red, binding_B
select binding_site, binding_A or binding_B
zoom binding_site
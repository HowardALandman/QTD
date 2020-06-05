// Support structure for 1/4" foamboard QTD experiment base
height=139;     // 160 to equator, minus 15 for flange, minus 6 for foam thickness
angle=30;
r_max = 138;    // Lulzbot Taz bed size is 280 x 280, so r_max <= 140. 139 was too big (got slightly truncated).
r_mink = 5;     // Radius of rounding in minkowski.
r_ring = r_max - r_mink; // Outside radius of ring before minkowski
r_contact = 63; // radius of "top" surface that contacts sphere support
fillet = 3;

// Now we need to compute the strut transform parameters.
// This is a little tricky.
r_strut = 5;
// Aim for making the top of the strut just tangent to the inner cylinder.
// But adjust for strut diameter.
// Since the tangent point makes a right triangle with the center and strut point,
// we can compute all the lengths.
// h = strut base to center = r_ring - 1
strut_h = r_ring - 1;
// b = tangent to center = r_contact - r_strut
strut_b = r_contact - r_strut;
// Given the hypotenuse and one side, compute the remaining side.
strut_a = sqrt(strut_h*strut_h - strut_b*strut_b);
// Find sin and cos of angle in base plane at strut base.
strut_cos = strut_a / strut_h;
strut_sin = strut_b / strut_h;
// Compute the necesary deltas in X and Y.
strut_dx = strut_a * strut_cos;
strut_dy = strut_a * strut_sin;
// Compute the corresponding transform parameters.
strut_cx = strut_dx / height;
strut_cy = strut_dy / height;
// Transform for struts tilted left.
ML = [[  1,   0, -strut_cx, 0  ],
      [  0,   1, -strut_cy, 0  ],
      [  0,   0, 1,         0  ],
      [  0,   0, 0,         1  ]] ;
// Transform for struts tilted right. Same as left, except for sign of Y.
MR = [[  1,   0, -strut_cx, 0  ],
      [  0,   1,  strut_cy, 0  ],
      [  0,   0, 1,         0  ],
      [  0,   0, 0,         1  ]] ;
      
// Transform to taper central slot
// It needs to be 133+ at "top" here and 128+ at "bottom".
// This changes over "height" variable.
// So X=64 needs to scale to X=67
slot_x_bot = 128;
slot_x_top = 134;
slot_y = 21;    // 20 was a tight fit before acetone vapor bath, jammed after.
slot_delta_x = (slot_x_top - slot_x_bot) / 2;
slot_slope = slot_delta_x / height;
MSL = [[  1,   0, slot_slope, 0  ],
      [  0,   1, 0,          0  ],
      [  0,   0, 1,          0  ],
      [  0,   0, 0,          1  ]] ;
MSR = [[  1,   0, -slot_slope, 0  ],
      [  0,   1, 0,          0  ],
      [  0,   0, 1,          0  ],
      [  0,   0, 0,          1  ]] ;

difference() {
    union() {
        // main cylinder is slightly conical to match slope of bracket hull
        cylinder(r1=r_contact-slot_delta_x,r2=r_contact,h=height,$fa=5);
        //translate([0,0,height-40]) cylinder(r1=0,r2=69,h=40,$fa=5);
        cylinder(r1=80,r2=0,h=80,$fa=5);
        //cylinder(r=135,h=2);
        // bracket hull
        hull() {
            hull_x = slot_x_bot / 2;
            hull_y = slot_y / 2;
            multmatrix(MSL) translate([ hull_x, hull_y,0]) cylinder(r=10,h=height);
            multmatrix(MSL) translate([ hull_x,-hull_y,0]) cylinder(r=10,h=height);
            multmatrix(MSR) translate([-hull_x, hull_y,0]) cylinder(r=10,h=height);
            multmatrix(MSR) translate([-hull_x,-hull_y,0]) cylinder(r=10,h=height);
        }
        // base + struts, filleted by minkowski
        difference() {
            cylinder(r=140,h=height+1);
            minkowski() {
                difference() {
                    cylinder(r=143,h=height+2);
                    union() {
                        // base
                        minkowski() {
                            union() {
                                // base ring
                                difference() {
                                    cylinder(r=r_ring,h=1,$fa=5);
                                    cylinder(r=r_ring-2,h=10,center=true,$fa=5);
                                }
                                // base radial struts
                                for(a = [angle/2 : angle : 180]) {
                                    rotate([0,0,a]) translate([0,0,0.5]) cube([2*strut_h,1,1],center=true);
                                }
                            }
                            // hemisphere to round everything
                            intersection() {
                                sphere(r=r_mink+fillet,center=true,$fa=10);
                                cylinder(r=r_mink+fillet+1,h=r_mink+fillet+1);
                            }
                        }
                        // Hyperboloid struts
                        for(a = [angle/2 : angle : 360]) {
                            rotate([0,0,a]) union() {
                                // left leaning struts
                                multmatrix(ML) {
                                    translate([strut_h,0,0]) cylinder(r=5+fillet,h=height,$fa=10);
                                }
                                // right leaning struts
                                multmatrix(MR) {
                                    translate([strut_h,0,0]) cylinder(r=5+fillet,h=height,$fa=10);
                                }
                                // hemisphere at join
                                //translate([strut_h,0,0]) intersection() {
                                //    sphere(r=8,center=true,$fa=10);
                                //    cylinder(r=11,h=11);
                                //}
                            }
                        }
                    }
                }
                sphere(r=fillet,center=true);
            }
        }
    }
    union() {
        multmatrix(MSL) { cube([slot_x_bot,slot_y,300],center=true); }
        multmatrix(MSR) { cube([slot_x_bot,slot_y,300],center=true); }
    }
    translate([0,0,10]) cylinder(r1=53-slot_delta_x,r2=53,h=height,$fa=5);
}

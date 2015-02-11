!        generated by tapenade     (inria, tropics team)
!  tapenade 3.10 (r5363) -  9 sep 2014 09:53
!
!  differentiation of dim in forward (tangent) mode (with options i4 dr8 r8):
!   variations   of useful results: dim
!   with respect to varying inputs: x y
function dim_d(x, xd, y, yd, dim)
  use precision
  implicit none
  real(kind=realtype) :: x, y, z
  real(kind=realtype) :: xd, yd
  real(kind=realtype) :: dim
  real(kind=realtype) :: dim_d
  dim_d = xd - yd
  dim = x - y
  if (dim .lt. 0.0) then
    dim = 0.0
    dim_d = 0.0_8
  end if
end function dim_d

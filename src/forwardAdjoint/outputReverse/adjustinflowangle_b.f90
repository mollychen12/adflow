!        generated by tapenade     (inria, tropics team)
!  tapenade 3.10 (r5363) -  9 sep 2014 09:53
!
!  differentiation of adjustinflowangle in reverse (adjoint) mode (with options i4 dr8 r8 noisize):
!   gradient     of useful results: veldirfreestream dragdirection
!                liftdirection
!   with respect to varying inputs: alpha beta
!
!      ******************************************************************
!      *                                                                *
!      * file:          adjustinflowangle.f90                           *
!      * author:        c.a.(sandy) mader                               *
!      * starting date: 07-13-2011                                      *
!      * last modified: 07-13-2011                                      *
!      *                                                                *
!      ******************************************************************
!
subroutine adjustinflowangle_b(alpha, alphad, beta, betad, liftindex)
  use constants
  use inputphysics
  implicit none
!subroutine vars
  real(kind=realtype), intent(in) :: alpha, beta
  real(kind=realtype) :: alphad, betad
  integer(kind=inttype), intent(in) :: liftindex
!local vars
  real(kind=realtype), dimension(3) :: refdirection
! velocity direction given by the rotation of a unit vector
! initially aligned along the positive x-direction (1,0,0)
! 1) rotate alpha radians cw about y or z-axis
! 2) rotate beta radians ccw about z or y-axis
  refdirection(:) = zero
  refdirection(1) = one
! drag direction given by the rotation of a unit vector
! initially aligned along the positive x-direction (1,0,0)
! 1) rotate alpha radians cw about y or z-axis
! 2) rotate beta radians ccw about z or y-axis
  call pushreal8array(refdirection, 3)
  refdirection(:) = zero
  refdirection(1) = one
! lift direction given by the rotation of a unit vector
! initially aligned along the positive z-direction (0,0,1)
! 1) rotate alpha radians cw about y or z-axis
! 2) rotate beta radians ccw about z or y-axis
  call pushreal8array(refdirection, 3)
  refdirection(:) = zero
  refdirection(liftindex) = one
  alphad = 0.0_8
  betad = 0.0_8
  call getdirvector_b(refdirection, alpha, alphad, beta, betad, &
&               liftdirection, liftdirectiond, liftindex)
  call popreal8array(refdirection, 3)
  call getdirvector_b(refdirection, alpha, alphad, beta, betad, &
&               dragdirection, dragdirectiond, liftindex)
  call popreal8array(refdirection, 3)
  call getdirvector_b(refdirection, alpha, alphad, beta, betad, &
&               veldirfreestream, veldirfreestreamd, liftindex)
end subroutine adjustinflowangle_b

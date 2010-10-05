!
!      ******************************************************************
!      *                                                                *
!      * File:          mdUpdateRoutines.f90                            *
!      * Author:        Edwin van der Weide                             *
!      * Starting date: 01-14-2004                                      *
!      * Last modified: 06-12-2005                                      *
!      *                                                                *
!      ******************************************************************
!
       subroutine updateCoordinatesAllLevels
!
!      ******************************************************************
!      *                                                                *
!      * updateCoordinatesAllLevels updates the coordinates of all      *
!      * grid levels, assuming that the owned coordinates of the fine   *
!      * grid are known.                                                *
!      *                                                                *
!      ******************************************************************
!
       use block
       use iteration

!temp
       use inputTimeSpectral
       use blockPointers
       implicit none
!
!      Local variables.
!
       integer(kind=intType) :: nLevels, nn
       !temporary!
       integer(kind=intType) :: sps,i,j,k,n
!
!      ******************************************************************
!      *                                                                *
!      * Begin execution                                                *
!      *                                                                *
!      ******************************************************************
!
       ! Determine the halo coordinates of the fine level.

       call xhalo(groundLevel)

       ! Loop over the coarse grid levels; first the owned coordinates
       ! are determined, followed by the halo's.

       nLevels = ubound(flowDoms,2)
       do nn=(groundLevel+1),nLevels
         call coarseOwnedCoordinates(nn)
         call xhalo(nn)
       enddo

!!$       do sps = 1,nTimeIntervalsSpectral
!!$          do nn = 1,nDom
!!$             !call setpointers(nn,groundLevel,sps)
!!$             call setPointersAdj(nn,groundLevel,sps)
!!$             do i = 1,ie
!!$                do j = 1,je
!!$                   do k = 1,ke
!!$                      do n = 1,3
!!$                         print *,'xpost',x(i,j,k,n),globalNode(i,j,k),sps,nn,i,j,k,n
!!$                      end do
!!$                   end do
!!$                end do
!!$             end do
!!$          end do
!!$       end do
       end subroutine updateCoordinatesAllLevels

!      ==================================================================

       subroutine updateMetricsAllLevels
!
!      ******************************************************************
!      *                                                                *
!      * updateMetricsAllLevels recomputes the metrics on all grid      *
!      * levels. This routine is typically called when the coordinates  *
!      * have changed, but the connectivity remains the same, i.e. for  *
!      * moving or deforming mesh problems.                             *
!      *                                                                *
!      ******************************************************************
!
       use block
       use iteration
       implicit none
!
!      Local variables.
!
       integer(kind=intType) :: nLevels, nn
!
!      ******************************************************************
!      *                                                                *
!      * Begin execution                                                *
!      *                                                                *
!      ******************************************************************
!
       ! Loop over the grid levels and call metric and checkSymmetry.

       nLevels = ubound(flowDoms,2)
       do nn=groundLevel,nLevels
         call metric(nn)
         call checkSymmetry(nn)
       enddo

       end subroutine updateMetricsAllLevels

       subroutine updateGridVelocitiesAllLevels

!
!      ******************************************************************
!      *                                                                *
!      * updateGridVelocitesAllLevels recomputes the rotational         *
!      * parameters on all grid                                         *
!      * levels. This routine is typically called when the coordinates  *
!      * have changed, but the connectivity remains the same, i.e. for  *
!      * moving or deforming mesh problems.                             *
!      *                                                                *
!      ******************************************************************
!
       use block
       use iteration
       use section
       use monitor
       use inputTimeSpectral
       use inputPhysics
       implicit none

       !subroutine variables

       !Local Variables
       
       integer(kind=inttype):: mm,nnn

       real(kind=realType), dimension(nSections) :: t

       do mm=1,nTimeIntervalsSpectral
          
          ! Compute the time, which corresponds to this spectral solution.
          ! For steady and unsteady mode this is simply the restart time;
          ! for the spectral mode the periodic time must be taken into
          ! account, which can be different for every section.
          
          t = timeUnsteadyRestart
          
          if(equationMode == timeSpectral) then
             do nnn=1,nSections
                t(nnn) = t(nnn) + (mm-1)*sections(nnn)%timePeriod &
                     /         real(nTimeIntervalsSpectral,realType)
             enddo
          endif
          
          call gridVelocitiesFineLevel(.false., t, mm)
          call gridVelocitiesCoarseLevels(mm)
          call normalVelocitiesAllLevels(mm)
          
          call slipVelocitiesFineLevel(.false., t, mm)
          call slipVelocitiesCoarseLevels(mm)
          
       enddo
       
     end subroutine updateGridVelocitiesAllLevels


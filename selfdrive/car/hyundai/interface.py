#!/usr/bin/env python3
from cereal import car
from selfdrive.config import Conversions as CV
from selfdrive.car.hyundai.values import Ecu, ECU_FINGERPRINT, CAR, FINGERPRINTS, Buttons, FEATURES
from selfdrive.car import STD_CARGO_KG, scale_rot_inertia, scale_tire_stiffness, is_ecu_disconnected, gen_empty_fingerprint
from selfdrive.car.interfaces import CarInterfaceBase
from selfdrive.controls.lib.lateral_planner import LANE_CHANGE_SPEED_MIN
from common.params import Params

GearShifter = car.CarState.GearShifter
EventName = car.CarEvent.EventName
ButtonType = car.CarState.ButtonEvent.Type

class CarInterface(CarInterfaceBase):
  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)
    self.cp2 = self.CS.get_can2_parser(CP)
    self.mad_mode_enabled = Params().get_bool('MadModeEnabled')

  @staticmethod
  def compute_gb(accel, speed):
    return float(accel) / 3.0

  @staticmethod
  def get_params(candidate, fingerprint=gen_empty_fingerprint(), has_relay=False, car_fw=[]):  # pylint: disable=dangerous-default-value
    ret = CarInterfaceBase.get_std_params(candidate, fingerprint, has_relay)

    ret.openpilotLongitudinalControl = Params().get_bool('LongControlEnabled')

    ret.carName = "hyundai"
    ret.safetyModel = car.CarParams.SafetyModel.hyundaiLegacy
    if candidate in [CAR.SONATA]:
      ret.safetyModel = car.CarParams.SafetyModel.hyundai

    # Most Hyundai car ports are community features for now
    ret.communityFeature = candidate not in [CAR.SONATA, CAR.PALISADE]

    ret.steerActuatorDelay = 0.1  # Default delay
    ret.steerRateCost = 0.5
    ret.steerLimitTimer = 0.8
    tire_stiffness_factor = 1.

    ret.maxSteeringAngleDeg = 90.
    ret.startAccel = 1.0

    eps_modified = False
    for fw in car_fw:
      if fw.ecu == "eps" and b"," in fw.fwVersion:
        eps_modified = True

    # genesis
    if candidate == CAR.GENESIS:
      ret.mass = 1900. + STD_CARGO_KG
      ret.wheelbase = 3.01
    elif candidate == CAR.GENESIS_G70:
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.84
    elif candidate == CAR.GENESIS_G80:
      ret.mass = 1855. + STD_CARGO_KG
      ret.wheelbase = 3.01
    elif candidate == CAR.GENESIS_G90:
      ret.mass = 2120
      ret.wheelbase = 3.16

    elif candidate == CAR.GENESIS_G90_L:
      ret.mass = 2290
      ret.wheelbase = 3.45
      ret.maxSteeringAngleDeg = 120.
    # hyundai
    elif candidate in [CAR.SANTA_FE]:
      ret.mass = 1694 + STD_CARGO_KG
      ret.wheelbase = 2.766
    elif candidate in [CAR.SONATA, CAR.SONATA_HEV]:
      ret.mass = 1513. + STD_CARGO_KG
      ret.wheelbase = 2.84
      tire_stiffness_factor = 0.65
    elif candidate in [CAR.SONATA19, CAR.SONATA19_HEV]:
      ret.mass = 4497. * CV.LB_TO_KG
      ret.wheelbase = 2.804
    elif candidate == CAR.SONATA_LF_TURBO:
      ret.mass = 1590. + STD_CARGO_KG
      ret.wheelbase = 2.805
      tire_stiffness_factor = 0.65
    elif candidate == CAR.PALISADE:
      ret.mass = 1999. + STD_CARGO_KG
      ret.wheelbase = 2.90
      if eps_modified:
        ret.maxSteeringAngleDeg = 1000.
    elif candidate in [CAR.ELANTRA, CAR.ELANTRA_GT_I30]:
      ret.mass = 1275. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385    # stiffnessFactor settled on 1.0081302973865127
    elif candidate == CAR.KONA:
      ret.mass = 1275. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.KONA_HEV, CAR.KONA_EV]:
      ret.mass = 1395. + STD_CARGO_KG
      ret.wheelbase = 2.6
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.IONIQ, CAR.IONIQ_EV_LTD]:
      ret.mass = 1490. + STD_CARGO_KG   #weight per hyundai site https://www.hyundaiusa.com/ioniq-electric/specifications.aspx
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.GRANDEUR_IG, CAR.GRANDEUR_IG_HEV]:
      tire_stiffness_factor = 0.8
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.845
      ret.maxSteeringAngleDeg = 120.
    elif candidate in [CAR.GRANDEUR_IG_FL, CAR.GRANDEUR_IG_FL_HEV]:
      tire_stiffness_factor = 0.8
      ret.mass = 1640. + STD_CARGO_KG
      ret.wheelbase = 2.845
      ret.maxSteeringAngleDeg = 120.
    elif candidate == CAR.VELOSTER:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    # kia
    elif candidate == CAR.SORENTO:
      ret.mass = 1985. + STD_CARGO_KG
      ret.wheelbase = 2.78
      tire_stiffness_factor = 0.5
    elif candidate in [CAR.K5, CAR.K5_HEV]:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    elif candidate == CAR.STINGER:
      tire_stiffness_factor = 1.125 # LiveParameters (Tunder's 2020)
      ret.mass = 1825.0 + STD_CARGO_KG
      ret.wheelbase = 2.906 # https://www.kia.com/us/en/stinger/specs
    elif candidate == CAR.FORTE:
      ret.mass = 3558. * CV.LB_TO_KG
      ret.wheelbase = 2.80
      tire_stiffness_factor = 0.5
    elif candidate == CAR.CEED:
      ret.mass = 1350. + STD_CARGO_KG
      ret.wheelbase = 2.65
      tire_stiffness_factor = 0.5
    elif candidate == CAR.SPORTAGE:
      ret.mass = 1985. + STD_CARGO_KG
      ret.wheelbase = 2.78
    elif candidate in [CAR.NIRO_HEV, CAR.NIRO_EV]:
      ret.mass = 1737. + STD_CARGO_KG
      ret.wheelbase = 2.7
      tire_stiffness_factor = 0.385
    elif candidate in [CAR.K7, CAR.K7_HEV]:
      tire_stiffness_factor = 0.6
      ret.mass = 1650. + STD_CARGO_KG
      ret.wheelbase = 2.855
    elif candidate == CAR.SELTOS:
      ret.mass = 1310. + STD_CARGO_KG
      ret.wheelbase = 2.6
      tire_stiffness_factor = 0.5


    ret.lateralTuning.init('lqr')

    ret.lateralTuning.lqr.scale = 1600.
    ret.lateralTuning.lqr.ki = 0.01
    ret.lateralTuning.lqr.dcGain = 0.00273

    ret.lateralTuning.lqr.a = [0., 1., -0.22619643, 1.21822268]
    ret.lateralTuning.lqr.b = [-1.92006585e-04, 3.95603032e-05]
    ret.lateralTuning.lqr.c = [1., 0.]
    ret.lateralTuning.lqr.k = [-110., 451.]
    ret.lateralTuning.lqr.l = [0.33, 0.318]

    ret.steerRatio = 16.5
    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 2.5

    ret.steerRateCost = 0.4

    ret.steerMaxBP = [0.]
    ret.steerMaxV = [1.5]


    if ret.openpilotLongitudinalControl:

#      ret.longitudinalTuning.kpBP = [0., 10. * CV.KPH_TO_MS, 20. * CV.KPH_TO_MS, 40. * CV.KPH_TO_MS, 100. * CV.KPH_TO_MS]
#      ret.longitudinalTuning.kpV = [0.97, 0.82, 0.63, 0.58, 0.43]
#      ret.longitudinalTuning.kiBP = [0.]
#      ret.longitudinalTuning.kiV = [0.015]
#      ret.longitudinalTuning.kf = 0.55
#      ret.longitudinalTuning.deadzoneBP = [0., 100.*CV.KPH_TO_MS]
#      ret.longitudinalTuning.deadzoneV = [0., 0.015]

#      ret.gasMaxBP = [0., 10.*CV.KPH_TO_MS, 20.*CV.KPH_TO_MS, 70.*CV.KPH_TO_MS, 130.*CV.KPH_TO_MS ]
#      ret.gasMaxV = [0.4, 0.28, 0.19, 0.12, 0.08]

#      ret.brakeMaxBP = [0.]
#      ret.brakeMaxV = [1.3]

#      ret.stoppingBrakeRate = 0.2  # brake_travel/s while trying to stop
#      ret.startingBrakeRate = 0.8  # brake_travel/s while releasing on restart
#      ret.startAccel = 1.7

      ret.longitudinalTuning.kpBP = [0., 15. * CV.KPH_TO_MS, 35. * CV.KPH_TO_MS, 50. * CV.KPH_TO_MS, 55. * CV.KPH_TO_MS, 70. * CV.KPH_TO_MS, 100. * CV.KPH_TO_MS]
      ret.longitudinalTuning.kpV = [0.6, 0.6551, 0.6641, 0.6325, 0.458, 0.45, 0.45]
      ret.longitudinalTuning.kiBP = [0., 126.*CV.KPH_TO_MS]
      ret.longitudinalTuning.kiV = [0.015, 0.02]
      ret.longitudinalTuning.kf = 0.5
      ret.longitudinalTuning.deadzoneBP = [0., 50.*CV.KPH_TO_MS, 100.*CV.KPH_TO_MS]
      ret.longitudinalTuning.deadzoneV = [0., 0., 0.015]

      ret.gasMaxBP = [0., 5.*CV.KPH_TO_MS, 10.*CV.KPH_TO_MS, 30.*CV.KPH_TO_MS, 36.*CV.KPH_TO_MS, 37.*CV.KPH_TO_MS, 48.*CV.KPH_TO_MS, 55.*CV.KPH_TO_MS, 70.*CV.KPH_TO_MS, 100.*CV.KPH_TO_MS]
      ret.gasMaxV = [0.1, 0.4443, 0.6062, 0.5594, 0.4284, 0.3744, 0.1805, 0.13, 0.12, 0.1] 
      ret.brakeMaxBP = [0., 10.*CV.KPH_TO_MS, 29.*CV.KPH_TO_MS, 30.*CV.KPH_TO_MS, 50*CV.KPH_TO_MS, 65*CV.KPH_TO_MS]
      ret.brakeMaxV = [0.28, 0.5533, 0.85201, 0.86601, 0.85601, 0.8380]

      ret.stoppingBrakeRate = 0.155  # brake_travel/s while trying to stop
      ret.startingBrakeRate = 0.99  # brake_travel/s while releasing on restart
      ret.startAccel = 1.1

    else:
      # scc smoother
      ret.longitudinalTuning.kpBP = [0., 10. * CV.KPH_TO_MS, 40. * CV.KPH_TO_MS, 100. * CV.KPH_TO_MS]
      ret.longitudinalTuning.kpV = [1.3, 1.2, 1.0, 0.45]
      ret.longitudinalTuning.kiBP = [0.]
      ret.longitudinalTuning.kiV = [0.]
      ret.longitudinalTuning.deadzoneBP = [0., 40]
      ret.longitudinalTuning.deadzoneV = [0., 0.02]

      ret.gasMaxBP = [0.]
      ret.gasMaxV = [0.5]
      ret.brakeMaxBP = [0., 20.]
      ret.brakeMaxV = [1., 0.8]

    ret.radarTimeStep = 0.05
    ret.centerToFront = ret.wheelbase * 0.4

    # TODO: get actual value, for now starting with reasonable value for
    # civic and scaling by mass and wheelbase
    ret.rotationalInertia = scale_rot_inertia(ret.mass, ret.wheelbase)

    # TODO: start from empirically derived lateral slip stiffness for the civic and scale by
    # mass and CG position, so all cars will have approximately similar dyn behaviors
    ret.tireStiffnessFront, ret.tireStiffnessRear = scale_tire_stiffness(ret.mass, ret.wheelbase, ret.centerToFront,
                                                                         tire_stiffness_factor=tire_stiffness_factor)

    # no rear steering, at least on the listed cars above
    ret.steerRatioRear = 0.
    ret.steerControlType = car.CarParams.SteerControlType.torque

    ret.enableCamera = is_ecu_disconnected(fingerprint[0], FINGERPRINTS, ECU_FINGERPRINT, candidate, Ecu.fwdCamera) or has_relay
    ret.stoppingControl = True

    # ignore CAN2 address if L-CAN on the same BUS
    ret.mdpsBus = 1 if 593 in fingerprint[1] and 1296 not in fingerprint[1] else 0
    ret.sasBus = 1 if 688 in fingerprint[1] and 1296 not in fingerprint[1] else 0
    ret.sccBus = 0 if 1056 in fingerprint[0] else 1 if 1056 in fingerprint[1] and 1296 not in fingerprint[1] \
                                                                     else 2 if 1056 in fingerprint[2] else -1

    print("!!!!! BUS", "MDPS", ret.mdpsBus, "SAS", ret.sasBus, "SCC", ret.sccBus)

    ret.radarOffCan = ret.sccBus == -1
    ret.enableCruise = not ret.radarOffCan

    # set safety_hyundai_community only for non-SCC, MDPS harrness or SCC harrness cars or cars that have unknown issue
    if ret.radarOffCan or ret.mdpsBus == 1 or ret.openpilotLongitudinalControl or ret.sccBus == 1 or Params().get_bool('MadModeEnabled'):
      ret.safetyModel = car.CarParams.SafetyModel.hyundaiCommunity
    return ret

  def update(self, c, can_strings):
    self.cp.update_strings(can_strings)
    self.cp2.update_strings(can_strings)
    self.cp_cam.update_strings(can_strings)

    ret = self.CS.update(self.cp, self.cp2, self.cp_cam)
    ret.canValid = self.cp.can_valid and self.cp2.can_valid and self.cp_cam.can_valid

    if self.CP.enableCruise and not self.CC.scc_live:
      self.CP.enableCruise = False
    elif self.CC.scc_live and not self.CP.enableCruise:
      self.CP.enableCruise = True

    # most HKG cars has no long control, it is safer and easier to engage by main on

    if self.mad_mode_enabled:
      ret.cruiseState.enabled = ret.cruiseState.available

    # turning indicator alert logic
    if (ret.leftBlinker or ret.rightBlinker or self.CC.turning_signal_timer) and ret.vEgo < LANE_CHANGE_SPEED_MIN - 1.2:
      self.CC.turning_indicator_alert = True
    else:
      self.CC.turning_indicator_alert = False

    # low speed steer alert hysteresis logic (only for cars with steer cut off above 10 m/s)
    if ret.vEgo < (self.CP.minSteerSpeed + 0.2) and self.CP.minSteerSpeed > 10.:
      self.low_speed_alert = True
    if ret.vEgo > (self.CP.minSteerSpeed + 0.7):
      self.low_speed_alert = False

    buttonEvents = []
    if self.CS.cruise_buttons != self.CS.prev_cruise_buttons:
      be = car.CarState.ButtonEvent.new_message()
      be.pressed = self.CS.cruise_buttons != 0
      but = self.CS.cruise_buttons if be.pressed else self.CS.prev_cruise_buttons
      if but == Buttons.RES_ACCEL:
        be.type = ButtonType.accelCruise
      elif but == Buttons.SET_DECEL:
        be.type = ButtonType.decelCruise
      elif but == Buttons.GAP_DIST:
        be.type = ButtonType.gapAdjustCruise
      #elif but == Buttons.CANCEL:
      #  be.type = ButtonType.cancel
      else:
        be.type = ButtonType.unknown
      buttonEvents.append(be)
    if self.CS.cruise_main_button != self.CS.prev_cruise_main_button:
      be = car.CarState.ButtonEvent.new_message()
      be.type = ButtonType.altButton3
      be.pressed = bool(self.CS.cruise_main_button)
      buttonEvents.append(be)
    ret.buttonEvents = buttonEvents

    events = self.create_common_events(ret)

    if self.CC.longcontrol and self.CS.cruise_unavail:
      events.add(EventName.brakeUnavailable)
    #if abs(ret.steeringAngleDeg) > 90. and EventName.steerTempUnavailable not in events.events:
    #  events.add(EventName.steerTempUnavailable)
    if self.low_speed_alert and not self.CS.mdps_bus:
      events.add(EventName.belowSteerSpeed)
    if self.CC.turning_indicator_alert:
      events.add(EventName.turningIndicatorOn)
    #if self.CS.lkas_button_on != self.CS.prev_lkas_button:
    #  events.add(EventName.buttonCancel)
    if self.mad_mode_enabled and EventName.pedalPressed in events.events:
      events.events.remove(EventName.pedalPressed)

  # handle button presses
    for b in ret.buttonEvents:
      # do disable on button down
      if b.type == ButtonType.cancel and b.pressed:
        events.add(EventName.buttonCancel)
      if self.CC.longcontrol and not self.CC.scc_live:
        # do enable on both accel and decel buttons
        if b.type in [ButtonType.accelCruise, ButtonType.decelCruise] and not b.pressed:
          events.add(EventName.buttonEnable)
        if EventName.wrongCarMode in events.events:
          events.events.remove(EventName.wrongCarMode)
        if EventName.pcmDisable in events.events:
          events.events.remove(EventName.pcmDisable)
      elif not self.CC.longcontrol and ret.cruiseState.enabled:
        # do enable on decel button only
        if b.type == ButtonType.decelCruise and not b.pressed:
          events.add(EventName.buttonEnable)

    # scc smoother
    if self.CC.scc_smoother is not None:
      self.CC.scc_smoother.inject_events(events)

    ret.events = events.to_msg()

    self.CS.out = ret.as_reader()
    return self.CS.out

  # scc smoother - hyundai only
  def apply(self, c, controls):
    can_sends = self.CC.update(c.enabled, self.CS, self.frame, c, c.actuators,
                               c.cruiseControl.cancel, c.hudControl.visualAlert, c.hudControl.leftLaneVisible,
                               c.hudControl.rightLaneVisible, c.hudControl.leftLaneDepart, c.hudControl.rightLaneDepart,
                               c.hudControl.setSpeed, c.hudControl.leadVisible, controls)
    self.frame += 1
    return can_sends

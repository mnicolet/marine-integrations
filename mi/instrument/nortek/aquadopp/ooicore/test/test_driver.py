"""
@package mi.instrument.nortek.aquadopp.ooicore.test.test_driver
@author Rachel Manoni
@brief Test cases for ooicore driver

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/test_driver
       $ bin/test_driver -u
       $ bin/test_driver -i
       $ bin/test_driver -q

   * From pyon
       $ bin/nosetests -s -v /Users/Bill/WorkSpace/marine-integrations/mi/instrument/nortek/aquadopp/ooicore
       $ bin/nosetests -s -v /Users/Bill/WorkSpace/marine-integrations/mi/instrument/nortek/aquadopp/ooicore -a UNIT
       $ bin/nosetests -s -v /Users/Bill/WorkSpace/marine-integrations/mi/instrument/nortek/aquadopp/ooicore -a INT
       $ bin/nosetests -s -v /Users/Bill/WorkSpace/marine-integrations/mi/instrument/nortek/aquadopp/ooicore -a QUAL
"""
import re
from mi.instrument.ooici.mi.test_driver.test.test_driver import DriverTestMixinSub

__author__ = 'Rachel Manoni'
__license__ = 'Apache 2.0'

from gevent import monkey; monkey.patch_all()
import gevent


from nose.plugins.attrib import attr

from mi.core.log import get_logger; log = get_logger()

from mi.idk.unit_test import InstrumentDriverTestCase, ParameterTestConfigKey

from mi.core.instrument.instrument_driver import DriverAsyncEvent

from mi.core.instrument.data_particle import DataParticleKey, DataParticleValue
from mi.core.instrument.chunker import StringChunker

from mi.core.exceptions import SampleException

from mi.instrument.nortek.aquadopp.ooicore.driver import DataParticleType
from mi.instrument.nortek.aquadopp.ooicore.driver import Protocol
from mi.instrument.nortek.aquadopp.ooicore.driver import AquadoppDwDiagnosticHeaderDataParticle
from mi.instrument.nortek.aquadopp.ooicore.driver import AquadoppDwDiagnosticHeaderDataParticleKey
from mi.instrument.nortek.aquadopp.ooicore.driver import AquadoppDwVelocityDataParticle
from mi.instrument.nortek.aquadopp.ooicore.driver import AquadoppDwVelocityDataParticleKey
from mi.instrument.nortek.aquadopp.ooicore.driver import AquadoppDwDiagnosticDataParticle

from mi.instrument.nortek.test.test_driver import NortekUnitTest, NortekIntTest, NortekQualTest
from mi.instrument.nortek.driver import ProtocolState, ProtocolEvent, NortekDataParticleType, TIMEOUT, ID_DATA_PATTERN

###
#   Driver parameters for the tests
###
InstrumentDriverTestCase.initialize(
    driver_module='mi.instrument.nortek.aquadopp.ooicore.driver',
    driver_class="InstrumentDriver",

    instrument_agent_resource_id='nortek_aquadopp_dw_ooicore',
    instrument_agent_name='nortek_aquadopp_dw_ooicore_agent',
    instrument_agent_packet_config=DataParticleType(),
    driver_startup_config={}
)


def user_config2():
    # CompassUpdateRate = 2, MeasurementInterval = 3600
    user_config_values = [0xa5, 0x00, 0x00, 0x01, 0x7d, 0x00, 0x37, 0x00, 0x20, 0x00, 0xb5, 0x01, 0x00, 0x02, 0x01, 0x00, 
                          0x3c, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 
                          0x01, 0x00, 0x01, 0x00, 0x20, 0x00, 0x10, 0x0e, 0x74, 0x65, 0x73, 0x74, 0x00, 0x00, 0x01, 0x00, 
                          0x56, 0x07, 0x08, 0x10, 0x12, 0x08, 0xc0, 0xa8, 0x00, 0x00, 0x22, 0x00, 0x11, 0x41, 0x14, 0x00, 
                          0x01, 0x00, 0x14, 0x00, 0x04, 0x00, 0x00, 0x00, 0xe8, 0x35, 0x5e, 0x01, 0x02, 0x3d, 0x1e, 0x3d, 
                          0x39, 0x3d, 0x53, 0x3d, 0x6e, 0x3d, 0x88, 0x3d, 0xa2, 0x3d, 0xbb, 0x3d, 0xd4, 0x3d, 0xed, 0x3d, 
                          0x06, 0x3e, 0x1e, 0x3e, 0x36, 0x3e, 0x4e, 0x3e, 0x65, 0x3e, 0x7d, 0x3e, 0x93, 0x3e, 0xaa, 0x3e, 
                          0xc0, 0x3e, 0xd6, 0x3e, 0xec, 0x3e, 0x02, 0x3f, 0x17, 0x3f, 0x2c, 0x3f, 0x41, 0x3f, 0x55, 0x3f, 
                          0x69, 0x3f, 0x7d, 0x3f, 0x91, 0x3f, 0xa4, 0x3f, 0xb8, 0x3f, 0xca, 0x3f, 0xdd, 0x3f, 0xf0, 0x3f, 
                          0x02, 0x40, 0x14, 0x40, 0x26, 0x40, 0x37, 0x40, 0x49, 0x40, 0x5a, 0x40, 0x6b, 0x40, 0x7c, 0x40, 
                          0x8c, 0x40, 0x9c, 0x40, 0xac, 0x40, 0xbc, 0x40, 0xcc, 0x40, 0xdb, 0x40, 0xea, 0x40, 0xf9, 0x40, 
                          0x08, 0x41, 0x17, 0x41, 0x25, 0x41, 0x33, 0x41, 0x42, 0x41, 0x4f, 0x41, 0x5d, 0x41, 0x6a, 0x41, 
                          0x78, 0x41, 0x85, 0x41, 0x92, 0x41, 0x9e, 0x41, 0xab, 0x41, 0xb7, 0x41, 0xc3, 0x41, 0xcf, 0x41, 
                          0xdb, 0x41, 0xe7, 0x41, 0xf2, 0x41, 0xfd, 0x41, 0x08, 0x42, 0x13, 0x42, 0x1e, 0x42, 0x28, 0x42, 
                          0x33, 0x42, 0x3d, 0x42, 0x47, 0x42, 0x51, 0x42, 0x5b, 0x42, 0x64, 0x42, 0x6e, 0x42, 0x77, 0x42, 
                          0x80, 0x42, 0x89, 0x42, 0x91, 0x42, 0x9a, 0x42, 0xa2, 0x42, 0xaa, 0x42, 0xb2, 0x42, 0xba, 0x42, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1e, 0x00, 0x5a, 0x00, 0x5a, 0x00, 0xbc, 0x02, 
                          0x32, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1e, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2a, 0x00, 0x00, 0x00, 
                          0x02, 0x00, 0x14, 0x00, 0xea, 0x01, 0x14, 0x00, 0xea, 0x01, 0x0a, 0x00, 0x05, 0x00, 0x00, 0x00, 
                          0x40, 0x00, 0x40, 0x00, 0x02, 0x00, 0x0f, 0x00, 0x5a, 0x00, 0x00, 0x00, 0x01, 0x00, 0xc8, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x0f, 0x00, 0xea, 0x01, 0xea, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x00, 
                          0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0a, 0xff, 
                          0xcd, 0xff, 0x8b, 0x00, 0xe5, 0x00, 0xee, 0x00, 0x0b, 0x00, 0x84, 0xff, 0x3d, 0xff, 0xa8, 0x98]
    user_config = ''
    for value in user_config_values:
        user_config += chr(value)
    return user_config


# velocity data particle & sample 
def velocity_sample():
    sample_as_hex = "a5011500101926221211000000009300f83b810628017f01002d0000e3094c0122ff9afe1e1416006093"
    return sample_as_hex.decode('hex')

velocity_particle = [{'value_id': 'date_time_string', 'value': '26/11/2012 22:10:19'},
                     {'value_id': 'error_code', 'value': 0},
                     {'value_id': 'analog1', 'value': 0}, 
                     {'value_id': 'battery_voltage', 'value': 147}, 
                     {'value_id': 'sound_speed_analog2', 'value': 15352}, 
                     {'value_id': 'heading', 'value': 1665}, 
                     {'value_id': 'pitch', 'value': 296}, 
                     {'value_id': 'roll', 'value': 383}, 
                     {'value_id': 'status', 'value': 45}, 
                     {'value_id': 'pressure', 'value': 0}, 
                     {'value_id': 'temperature', 'value': 2531}, 
                     {'value_id': 'velocity_beam1', 'value': 332}, 
                     {'value_id': 'velocity_beam2', 'value': 65314}, 
                     {'value_id': 'velocity_beam3', 'value': 65178}, 
                     {'value_id': 'amplitude_beam1', 'value': 30}, 
                     {'value_id': 'amplitude_beam2', 'value': 20}, 
                     {'value_id': 'amplitude_beam3', 'value': 22}]


# diagnostic header data particle & sample 
def diagnostic_header_sample():
    sample_as_hex = "a5061200140001000000000011192622121100000000000000000000000000000000a108"
    return sample_as_hex.decode('hex')

diagnostic_header_particle = [{'value_id': 'records_to_follow', 'value': 20},
                              {'value_id': 'cell_number_diagnostics', 'value': 1},
                              {'value_id': 'noise_amplitude_beam1', 'value': 0},
                              {'value_id': 'noise_amplitude_beam2', 'value': 0},
                              {'value_id': 'noise_amplitude_beam3', 'value': 0},
                              {'value_id': 'noise_amplitude_beam4', 'value': 0},
                              {'value_id': 'processing_magnitude_beam1', 'value': 6417}, 
                              {'value_id': 'processing_magnitude_beam2', 'value': 8742}, 
                              {'value_id': 'processing_magnitude_beam3', 'value': 4370}, 
                              {'value_id': 'processing_magnitude_beam4', 'value': 0}, 
                              {'value_id': 'distance_beam1', 'value': 0},
                              {'value_id': 'distance_beam2', 'value': 0},
                              {'value_id': 'distance_beam3', 'value': 0},
                              {'value_id': 'distance_beam4', 'value': 0}]


# diagnostic data particle & sample 
def diagnostic_sample():
    sample_as_hex = "a5801500112026221211000000009300f83ba0065c0189fe002c0000e40904ffd8ffbdfa18131500490f"
    return sample_as_hex.decode('hex')

diagnostic_particle = [{'value_id': 'date_time_string', 'value': '26/11/2012 22:11:20'},
                       {'value_id': 'error_code', 'value': 0},
                       {'value_id': 'analog1', 'value': 0}, 
                       {'value_id': 'battery_voltage', 'value': 147}, 
                       {'value_id': 'sound_speed_analog2', 'value': 15352}, 
                       {'value_id': 'heading', 'value': 1696}, 
                       {'value_id': 'pitch', 'value': 348}, 
                       {'value_id': 'roll', 'value': 65161}, 
                       {'value_id': 'status', 'value': 44}, 
                       {'value_id': 'pressure', 'value': 0}, 
                       {'value_id': 'temperature', 'value': 2532}, 
                       {'value_id': 'velocity_beam1', 'value': 65284}, 
                       {'value_id': 'velocity_beam2', 'value': 65496}, 
                       {'value_id': 'velocity_beam3', 'value': 64189}, 
                       {'value_id': 'amplitude_beam1', 'value': 24},                        
                       {'value_id': 'amplitude_beam2', 'value': 19}, 
                       {'value_id': 'amplitude_beam3', 'value': 21}]


###############################################################################
#                           DRIVER TEST MIXIN        		                  #
#     Defines a set of constants and assert methods used for data particle    #
#     verification 														      #
#                                                                             #
#  In python, mixin classes are classes designed such that they wouldn't be   #
#  able to stand on their own, but are inherited by other classes generally   #
#  using multiple inheritance.                                                #
#                                                                             #
# This class defines a configuration structure for testing and common assert  #
# methods for validating data particles.									  #
###############################################################################
class AquadoppDriverTestMixinSub(DriverTestMixinSub):
    """
    Mixin class used for storing data particle constance and common data assertion methods.
    """

    #Create some short names for the parameter test config
    TYPE = ParameterTestConfigKey.TYPE
    READONLY = ParameterTestConfigKey.READONLY
    STARTUP = ParameterTestConfigKey.STARTUP
    DA = ParameterTestConfigKey.DIRECT_ACCESS
    VALUE = ParameterTestConfigKey.VALUE
    REQUIRED = ParameterTestConfigKey.REQUIRED
    DEFAULT = ParameterTestConfigKey.DEFAULT
    STATES = ParameterTestConfigKey.STATES

    _sample_diagnostic_header = {
        AquadoppDwDiagnosticHeaderDataParticleKey.RECORDS: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.CELL: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.NOISE1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.NOISE2: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.NOISE3: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.NOISE4: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.PROCESSING_MAGNITUDE_BEAM1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.PROCESSING_MAGNITUDE_BEAM2: {TYPE: int, VALUE: 1, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.PROCESSING_MAGNITUDE_BEAM3: {TYPE: int, VALUE: 1, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.PROCESSING_MAGNITUDE_BEAM4: {TYPE: int, VALUE: 1, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.DISTANCE1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.DISTANCE2: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.DISTANCE3: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwDiagnosticHeaderDataParticleKey.DISTANCE4: {TYPE: int, VALUE: 0, REQUIRED: True}
    }

    #this particle can be used for both the velocity particle and the diagnostic particle
    _sample_velocity_diagnostic = {
        AquadoppDwVelocityDataParticleKey.TIMESTAMP: {TYPE: unicode, VALUE: '', REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.ERROR: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.ANALOG1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.BATTERY_VOLTAGE: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.SOUND_SPEED_ANALOG2: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.HEADING: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.PITCH: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.ROLL: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.PRESSURE: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.STATUS: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.TEMPERATURE: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.VELOCITY_BEAM1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.VELOCITY_BEAM2: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.VELOCITY_BEAM3: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.AMPLITUDE_BEAM1: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.AMPLITUDE_BEAM2: {TYPE: int, VALUE: 0, REQUIRED: True},
        AquadoppDwVelocityDataParticleKey.AMPLITUDE_BEAM3: {TYPE: int, VALUE: 0, REQUIRED: True}
    }

    def assert_particle_velocity(self, data_particle, verify_values=False):
        """
        Verify velpt_velocity_data
        @param data_particle:  AquadoppDwVelocityDataParticleKey data particle
        @param verify_values:
        """

        self.assert_data_particle_keys(AquadoppDwVelocityDataParticleKey, self._sample_velocity_diagnostic)
        self.assert_data_particle_header(data_particle, DataParticleType.VELOCITY)
        self.assert_data_particle_parameters(data_particle, self._sample_velocity_diagnostic, verify_values)

    def assert_particle_diagnostic_header(self, data_particle, verify_values=False):
        """
        Verify velpt_diagostics_header
        @param data_particle:  AquadoppDwDiagnosticHeaderDataParticleKey data particle
        @param verify_values:
        """

        self.assert_data_particle_keys(AquadoppDwDiagnosticHeaderDataParticleKey, self._sample_diagnostic_header)
        self.assert_data_particle_header(data_particle, DataParticleType.DIAGNOSTIC_HEADER)
        self.assert_data_particle_parameters(data_particle, self._sample_diagnostic_header, verify_values)

    def assert_particle_diagnostic(self, data_particle, verify_values=False):
        """
        Verify velpt_diagonstics_data
        @param data_particle:  AquadoppDwDiagnosticDataParticle data particle
        @param verify_values:  bool, should we verify parameter values
        """

        self.assert_data_particle_keys(AquadoppDwDiagnosticDataParticle, self._sample_velocity_diagnostic)
        self.assert_data_particle_header(data_particle, DataParticleType.DIAGNOSTIC)
        self.assert_data_particle_parameters(data_particle, self._sample_velocity_diagnostic, verify_values)


#################################### RULES ####################################
#                                                                             #
# Common capabilities in the base class                                       #
#                                                                             #
# Instrument specific stuff in the derived class                              #
#                                                                             #
# Generator spits out either stubs or comments describing test this here,     #
# test that there.                                                            #
#                                                                             #
# Qualification tests are driven through the instrument_agent                 #
#                                                                             #
###############################################################################
###############################################################################
#                                UNIT TESTS                                   #
#         Unit tests test the method calls and parameters using Mock.         #
###############################################################################
@attr('UNIT', group='mi')
class DriverUnitTest(NortekUnitTest):
    def setUp(self):
        NortekUnitTest.setUp(self)

    def test_driver_enums(self):
        """
        Verify driver specific enums have no duplicates
        Base unit test driver will test enums specific for the base class.
        """
        self.assert_enum_has_no_duplicates(DataParticleType())

    def test_diagnostic_header_sample_format(self):
        """
        Verify driver can get diagnostic_header sample data out in a reasonable format.
        Parsed is all we care about...raw is tested in the base DataParticle tests
        """
        port_timestamp = 3555423720.711772
        driver_timestamp = 3555423722.711772

        # construct the expected particle
        expected_particle = {
            DataParticleKey.PKT_FORMAT_ID: DataParticleValue.JSON_DATA,
            DataParticleKey.PKT_VERSION: 1,
            DataParticleKey.STREAM_NAME: DataParticleType.DIAGNOSTIC_HEADER,
            DataParticleKey.PORT_TIMESTAMP: port_timestamp,
            DataParticleKey.DRIVER_TIMESTAMP: driver_timestamp,
            DataParticleKey.PREFERRED_TIMESTAMP: DataParticleKey.PORT_TIMESTAMP,
            DataParticleKey.QUALITY_FLAG: DataParticleValue.OK,
            DataParticleKey.VALUES: diagnostic_header_particle}
        
        self.compare_parsed_data_particle(AquadoppDwDiagnosticHeaderDataParticle,
                                          diagnostic_header_sample(),
                                          expected_particle)

    def test_diagnostic_sample_format(self):
        """
        Verify driver can get diagnostic sample data out in a reasonable format.
        Parsed is all we care about...raw is tested in the base DataParticle tests
        """
        port_timestamp = 3555423720.711772
        driver_timestamp = 3555423722.711772

        # construct the expected particle
        expected_particle = {
            DataParticleKey.PKT_FORMAT_ID: DataParticleValue.JSON_DATA,
            DataParticleKey.PKT_VERSION: 1,
            DataParticleKey.STREAM_NAME: DataParticleType.DIAGNOSTIC,
            DataParticleKey.PORT_TIMESTAMP: port_timestamp,
            DataParticleKey.DRIVER_TIMESTAMP: driver_timestamp,
            DataParticleKey.PREFERRED_TIMESTAMP: DataParticleKey.PORT_TIMESTAMP,
            DataParticleKey.QUALITY_FLAG: DataParticleValue.OK,
            DataParticleKey.VALUES: diagnostic_particle}
        
        self.compare_parsed_data_particle(AquadoppDwDiagnosticDataParticle,
                                          diagnostic_sample(),
                                          expected_particle)

    def test_velocity_sample_format(self):
        """
        Verify driver can get velocity sample data out in a reasonable format.
        Parsed is all we care about...raw is tested in the base DataParticle tests
        """
        
        port_timestamp = 3555423720.711772
        driver_timestamp = 3555423722.711772

        # construct the expected particle
        expected_particle = {
            DataParticleKey.PKT_FORMAT_ID: DataParticleValue.JSON_DATA,
            DataParticleKey.PKT_VERSION: 1,
            DataParticleKey.STREAM_NAME: DataParticleType.VELOCITY,
            DataParticleKey.PORT_TIMESTAMP: port_timestamp,
            DataParticleKey.DRIVER_TIMESTAMP: driver_timestamp,
            DataParticleKey.PREFERRED_TIMESTAMP: DataParticleKey.PORT_TIMESTAMP,
            DataParticleKey.QUALITY_FLAG: DataParticleValue.OK,
            DataParticleKey.VALUES: velocity_particle}
        
        self.compare_parsed_data_particle(AquadoppDwVelocityDataParticle,
                                          velocity_sample(),
                                          expected_particle)

    def test_chunker(self):
        """
        Verify the chunker can parse each sample type
        1. complete data structure
        2. fragmented data structure
        3. combined data structure
        4. data structure with noise
        """
        chunker = StringChunker(Protocol.chunker_sieve_function)

        # test complete data structures
        self.assert_chunker_sample(chunker, velocity_sample())
        self.assert_chunker_sample(chunker, diagnostic_sample())
        self.assert_chunker_sample(chunker, diagnostic_header_sample())

        # test fragmented data structures
        self.assert_chunker_fragmented_sample(chunker, velocity_sample())
        self.assert_chunker_fragmented_sample(chunker, diagnostic_sample())
        self.assert_chunker_fragmented_sample(chunker, diagnostic_header_sample())

        # test combined data structures
        self.assert_chunker_combined_sample(chunker, velocity_sample())
        self.assert_chunker_combined_sample(chunker, diagnostic_sample())
        self.assert_chunker_combined_sample(chunker, diagnostic_header_sample())

        # test data structures with noise
        self.assert_chunker_sample_with_noise(chunker, velocity_sample())
        self.assert_chunker_sample_with_noise(chunker, diagnostic_sample())
        self.assert_chunker_sample_with_noise(chunker, diagnostic_header_sample())

    def test_corrupt_data_structures(self):
        """
        Verify when generating the particle, if the particle is corrupt, an exception is raised
        """
        particle = AquadoppDwDiagnosticHeaderDataParticle(diagnostic_header_sample().replace(chr(0), chr(1), 1),
                        port_timestamp=3558720820.531179)
        with self.assertRaises(SampleException):
            particle.generate()
         
        particle = AquadoppDwDiagnosticDataParticle(diagnostic_sample().replace(chr(0), chr(1), 1),
                        port_timestamp=3558720820.531179)
        with self.assertRaises(SampleException):
            particle.generate()
         
        particle = AquadoppDwVelocityDataParticle(velocity_sample().replace(chr(0), chr(1), 1),
                        port_timestamp=3558720820.531179)
        with self.assertRaises(SampleException):
            particle.generate()

 
###############################################################################
#                            INTEGRATION TESTS                                #
#     Integration test test the direct driver / instrument interaction        #
#     but making direct calls via zeromq.                                     #
#     - Common Integration tests test the driver through the instrument agent #
#     and common for all drivers (minimum requirement for ION ingestion)      #
###############################################################################
@attr('INT', group='mi')
class IntFromIDK(NortekIntTest, AquadoppDriverTestMixinSub):
    
    def setUp(self):
        NortekIntTest.setUp(self)

    def test_acquire_sample(self):
        """
        Test acquire sample command and events.
        1. initialize the instrument to COMMAND state
        2. command the driver to ACQUIRESAMPLE
        3. verify the particle coming in
        """

        self.assert_initialize_driver(ProtocolState.COMMAND)
        # test acquire sample
        self.assert_driver_command(ProtocolEvent.ACQUIRE_SAMPLE, state=ProtocolState.COMMAND, delay=1)
        self.assert_async_particle_generation(DataParticleType.VELOCITY, self.assert_particle_velocity, timeout=TIMEOUT)

    def test_command_autosample(self):
        """
        Test autosample command and events.
        1. initialize the instrument to COMMAND state
        2. command the instrument to AUTOSAMPLE state
        3. verify the particle coming in
        4. command the instrument back to COMMAND state
        5. verify the sampling is continuous by gathering several samples
        """

        self.assert_initialize_driver(ProtocolState.COMMAND)

        # test autosample
        self.assert_driver_command(ProtocolEvent.START_AUTOSAMPLE, state=ProtocolState.AUTOSAMPLE, delay=1)

        self.assert_async_particle_generation(NortekDataParticleType.USER_CONFIG, self.assert_particle_user, timeout=TIMEOUT)
        self.assert_async_particle_generation(DataParticleType.VELOCITY, self.assert_particle_velocity, timeout=TIMEOUT)

        # TODO - WHEN DOES THIS PARTICLE COME ABOUT?
        #self.assert_async_particle_generation(DataParticleType.DIAGNOSTIC_HEADER, self.assert_particle_diagnostic_header, timeout=TIMEOUT)
        #self.assert_async_particle_generation(DataParticleType.DIAGNOSTIC, self.assert_particle_diagnostic, timeout=TIMEOUT)

        # # wait for some samples to be generated
        gevent.sleep(10)

        # Verify we received at least 4 samples.
        sample_events = [evt for evt in self.events if evt['type'] == DriverAsyncEvent.SAMPLE]
        log.debug('test_instrument_acquire_sample: # 0f samples = %d', len(sample_events))
        log.debug('samples=%s', sample_events)
        self.assertTrue(len(sample_events) >= 4)

        self.assert_driver_command(ProtocolEvent.STOP_AUTOSAMPLE, state=ProtocolState.COMMAND, delay=1)
               
    def test_instrument_read_id(self):
        """
        Test for reading ID, need to be implemented in the child class because each ID is unique to the
        instrument.
        """
        self.assert_initialize_driver()

        # command the instrument to read the ID.
        response = self.driver_client.cmd_dvr('execute_resource', ProtocolEvent.READ_ID)

        log.debug("read ID returned: %s", response)
        self.assertTrue(re.search(r'AQD .*', response[1]))

        self.assert_driver_command(ProtocolEvent.READ_ID, regex=ID_DATA_PATTERN)

###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for                                 #
# testing device specific capabilities                                        #
###############################################################################
@attr('QUAL', group='mi')
class QualFromIDK(NortekQualTest):
    def setUp(self):
        NortekQualTest.setUp(self)

    def assert_sample_data_particle(self, sample):
        log.debug('assertSampleDataParticle: sample=%s', sample)
        self.assertTrue(sample[DataParticleKey.STREAM_NAME],
            DataParticleType.PARSED)
        self.assertTrue(sample[DataParticleKey.PKT_FORMAT_ID],
            DataParticleValue.JSON_DATA)
        self.assertTrue(sample[DataParticleKey.PKT_VERSION], 1)
        self.assertTrue(isinstance(sample[DataParticleKey.VALUES],
            list))
        self.assertTrue(isinstance(sample.get(DataParticleKey.DRIVER_TIMESTAMP), float))
        self.assertTrue(sample.get(DataParticleKey.PREFERRED_TIMESTAMP))
        
        values = sample['values']
        value_ids = []
        for value in values:
            value_ids.append(value['value_id'])
        if AquadoppDwVelocityDataParticleKey.TIMESTAMP in value_ids:
            log.debug('assertSampleDataParticle: AquadoppDwVelocityDataParticle/AquadoppDwDiagnosticDataParticle detected')
            self.assertEqual(sorted(value_ids), sorted(AquadoppDwVelocityDataParticleKey.list()))
            for value in values:
                if value['value_id'] == AquadoppDwVelocityDataParticleKey.TIMESTAMP:
                    self.assertTrue(isinstance(value['value'], str))
                else:
                    self.assertTrue(isinstance(value['value'], int))
        elif AquadoppDwDiagnosticHeaderDataParticleKey.RECORDS in value_ids:
            log.debug('assertSampleDataParticle: AquadoppDwDiagnosticHeaderDataParticle detected')
            self.assertEqual(sorted(value_ids), sorted(AquadoppDwDiagnosticHeaderDataParticleKey.list()))
            for value in values:
                self.assertTrue(isinstance(value['value'], int))
        else:
            self.fail('Unknown data particle')

    def test_direct_access_telnet_mode(self):
        """
        This test manually tests that the Instrument Driver properly supports direct access to the
        physical instrument. (telnet mode)
        """
        self.assert_direct_access_start_telnet()
        self.assertTrue(self.tcp_client)

        self.tcp_client.send_data("K1W%!Q")
        self.tcp_client.expect("DW-AQUADOPP")

        self.assert_direct_access_stop_telnet()

    def test_poll(self):
        """
        poll for a single sample
        Verify execute_acquire_sample
        """
        self.assert_sample_polled(self.assert_sample_data_particle,
                                  [DataParticleType.VELOCITY,
                                   DataParticleType.DIAGNOSTIC,
                                   DataParticleType.DIAGNOSTIC_HEADER],
                                  timeout=100)

    def test_autosample(self):
        """
        start and stop autosample and verify data particle
        Verify execute_start_autosample and execute_stop_autosample
        """
        self.assert_sample_autosample(self.assert_sample_data_particle,
                                  [DataParticleType.VELOCITY,
                                   DataParticleType.DIAGNOSTIC,
                                   DataParticleType.DIAGNOSTIC_HEADER],
                                  timeout=100)


// modification of https://github.com/fornpunkt/coordinate-parser
// for browser support

const Validator = class Validator {
  isValid(coordinates) {
    var isValid, validationError;
    isValid = true;
    try {
      this.validate(coordinates);
      return isValid;
    } catch (error) {
      validationError = error;
      isValid = false;
      return isValid;
    }
  }

  validate(coordinates) {
    this.checkContainsNoLetters(coordinates);
    this.checkValidOrientation(coordinates);
    return this.checkNumbers(coordinates);
  }

  checkContainsNoLetters(coordinates) {
    var containsLetters;
    containsLetters = /(?![neswd])[a-z]/i.test(coordinates);
    if (containsLetters) {
      throw new Error('Coordinate contains invalid alphanumeric characters.');
    }
  }

  checkValidOrientation(coordinates) {
    var validOrientation;
    validOrientation = /^[^nsew]*[ns]?[^nsew]*[ew]?[^nsew]*$/i.test(coordinates);
    if (!validOrientation) {
      throw new Error('Invalid cardinal direction.');
    }
  }

  checkNumbers(coordinates) {
    var coordinateNumbers;
    coordinateNumbers = coordinates.match(/-?\d+(\.\d+)?/g);
    this.checkAnyCoordinateNumbers(coordinateNumbers);
    this.checkEvenCoordinateNumbers(coordinateNumbers);
    return this.checkMaximumCoordinateNumbers(coordinateNumbers);
  }

  checkAnyCoordinateNumbers(coordinateNumbers) {
    if (coordinateNumbers.length === 0) {
      throw new Error('Could not find any coordinate number');
    }
  }

  checkEvenCoordinateNumbers(coordinateNumbers) {
    var isUnevenNumbers;
    isUnevenNumbers = coordinateNumbers.length % 2;
    if (isUnevenNumbers) {
      throw new Error('Uneven count of latitude/longitude numbers');
    }
  }

  checkMaximumCoordinateNumbers(coordinateNumbers) {
    if (coordinateNumbers.length > 6) {
      throw new Error('Too many coordinate numbers');
    }
  }

};

const CoordinateNumber = class CoordinateNumber {
  constructor(coordinateNumbers) {
    coordinateNumbers = this.normalizeCoordinateNumbers(coordinateNumbers);
    this.sign = this.normalizedSignOf(coordinateNumbers[0]);
    [this.degrees, this.minutes, this.seconds, this.milliseconds] = coordinateNumbers.map(Math.abs);
  }

  normalizeCoordinateNumbers(coordinateNumbers) {
    var currentNumber, i, j, len, normalizedNumbers;
    normalizedNumbers = [0, 0, 0, 0];
    for (i = j = 0, len = coordinateNumbers.length; j < len; i = ++j) {
      currentNumber = coordinateNumbers[i];
      normalizedNumbers[i] = parseFloat(currentNumber);
    }
    return normalizedNumbers;
  }

  normalizedSignOf(number) {
    if (number >= 0) {
      return 1;
    } else {
      return -1;
    }
  }

  detectSpecialFormats() {
    if (this.degreesCanBeSpecial()) {
      if (this.degreesCanBeMilliseconds()) {
        return this.degreesAsMilliseconds();
      } else if (this.degreesCanBeDegreesMinutesAndSeconds()) {
        return this.degreesAsDegreesMinutesAndSeconds();
      } else if (this.degreesCanBeDegreesAndMinutes()) {
        return this.degreesAsDegreesAndMinutes();
      }
    }
  }

  degreesCanBeSpecial() {
    var canBe;
    canBe = false;
    if (!this.minutes && !this.seconds) {
      canBe = true;
    }
    return canBe;
  }

  degreesCanBeMilliseconds() {
    var canBe;
    if (this.degrees > 909090) {
      canBe = true;
    } else {
      canBe = false;
    }
    return canBe;
  }

  degreesAsMilliseconds() {
    this.milliseconds = this.degrees;
    return this.degrees = 0;
  }

  degreesCanBeDegreesMinutesAndSeconds() {
    var canBe;
    if (this.degrees > 9090) {
      canBe = true;
    } else {
      canBe = false;
    }
    return canBe;
  }

  degreesAsDegreesMinutesAndSeconds() {
    var newDegrees;
    newDegrees = Math.floor(this.degrees / 10000);
    this.minutes = Math.floor((this.degrees - newDegrees * 10000) / 100);
    this.seconds = Math.floor(this.degrees - newDegrees * 10000 - this.minutes * 100);
    return this.degrees = newDegrees;
  }

  degreesCanBeDegreesAndMinutes() {
    var canBe;
    if (this.degrees > 360) {
      canBe = true;
    } else {
      canBe = false;
    }
    return canBe;
  }

  degreesAsDegreesAndMinutes() {
    var newDegrees;
    newDegrees = Math.floor(this.degrees / 100);
    this.minutes = this.degrees - newDegrees * 100;
    return this.degrees = newDegrees;
  }

  toDecimal() {
    var decimalCoordinate;
    decimalCoordinate = this.sign * (this.degrees + this.minutes / 60 + this.seconds / 3600 + this.milliseconds / 3600000);
    return decimalCoordinate;
  }

};

const Coordinates = class Coordinates {
  constructor(coordinateString) {
    this.coordinates = coordinateString;
    this.latitudeNumbers = null;
    this.longitudeNumbers = null;
    this.validate();
    this.parse();
  }

  validate() {
    var validator;
    validator = new Validator();
    return validator.validate(this.coordinates);
  }

  parse() {
    this.groupCoordinateNumbers();
    this.latitude = this.extractLatitude();
    return this.longitude = this.extractLongitude();
  }

  groupCoordinateNumbers() {
    var coordinateNumbers, numberCountEachCoordinate;
    coordinateNumbers = this.extractCoordinateNumbers(this.coordinates);
    numberCountEachCoordinate = coordinateNumbers.length / 2;
    this.latitudeNumbers = coordinateNumbers.slice(0, numberCountEachCoordinate);
    return this.longitudeNumbers = coordinateNumbers.slice((0 - numberCountEachCoordinate));
  }

  extractCoordinateNumbers(coordinates) {
    return coordinates.match(/-?\d+(\.\d+)?/g);
  }

  extractLatitude() {
    var latitude;
    latitude = this.coordinateNumbersToDecimal(this.latitudeNumbers);
    if (this.latitudeIsNegative()) {
      latitude = latitude * -1;
    }
    return latitude;
  }

  extractLongitude() {
    var longitude;
    longitude = this.coordinateNumbersToDecimal(this.longitudeNumbers);
    if (this.longitudeIsNegative()) {
      longitude = longitude * -1;
    }
    return longitude;
  }

  coordinateNumbersToDecimal(coordinateNumbers) {
    var coordinate, decimalCoordinate;
    coordinate = new CoordinateNumber(coordinateNumbers);
    coordinate.detectSpecialFormats();
    decimalCoordinate = coordinate.toDecimal();
    return decimalCoordinate;
  }

  latitudeIsNegative() {
    var isNegative;
    isNegative = this.coordinates.match(/s/i);
    return isNegative;
  }

  longitudeIsNegative() {
    var isNegative;
    isNegative = this.coordinates.match(/w/i);
    return isNegative;
  }

  getLatitude() {
    return this.latitude;
  }

  getLongitude() {
    return this.longitude;
  }

};

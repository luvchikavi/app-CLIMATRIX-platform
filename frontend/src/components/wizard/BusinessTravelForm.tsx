'use client';

/**
 * BusinessTravelForm - Category 3.6 Business Travel
 *
 * Supports 3 travel types per GHG Protocol:
 * 1. Flights - Air travel with cabin class (distance or spend)
 * 2. Hotels - Accommodation (nights or spend)
 * 3. Other Travel - Rail, taxi, rental car, bus (distance or spend)
 */

import { useState, useMemo } from 'react';
import { useWizardStore } from '@/stores/wizard';
import { useCreateActivity, useFlightDistance } from '@/hooks/useEmissions';
import { Button, Input } from '@/components/ui';
import { formatCO2e } from '@/lib/utils';
import {
  Calculator,
  Save,
  Plus,
  Loader2,
  ArrowLeft,
  Plane,
  Building2,
  Car,
  Train,
  Info,
  MapPin,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';

// =============================================================================
// BUSINESS TRAVEL DATA DEFINITIONS
// =============================================================================

type TravelType = 'flights' | 'hotels' | 'other';
type CalcMethod = 'distance' | 'spend' | 'physical';

// Cabin Classes for Flights
const CABIN_CLASSES = [
  { key: 'economy', label: 'Economy', multiplier: 1.0 },
  { key: 'premium_economy', label: 'Premium Economy', multiplier: 1.6 },
  { key: 'business', label: 'Business', multiplier: 2.9 },
  { key: 'first', label: 'First', multiplier: 4.0 },
];

// Trip Types
const TRIP_TYPES = [
  { key: 'one_way', label: 'One Way', multiplier: 1 },
  { key: 'round_trip', label: 'Round Trip', multiplier: 2 },
];

// Other Travel Types
const OTHER_TRAVEL_TYPES = [
  { key: 'rail', label: 'Rail/Train', ef: 0.035, icon: Train },
  { key: 'taxi', label: 'Taxi', ef: 0.21, icon: Car },
  { key: 'rental_car', label: 'Rental Car', ef: 0.17, icon: Car },
  { key: 'bus', label: 'Bus', ef: 0.089, icon: Car },
  { key: 'metro', label: 'Metro/Subway', ef: 0.029, icon: Train },
  { key: 'ferry', label: 'Ferry', ef: 0.19, icon: Car },
];

// Common Countries for Hotels
const COUNTRIES = [
  { code: 'IL', name: 'Israel' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'US', name: 'United States' },
  { code: 'DE', name: 'Germany' },
  { code: 'FR', name: 'France' },
  { code: 'IT', name: 'Italy' },
  { code: 'ES', name: 'Spain' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'JP', name: 'Japan' },
  { code: 'CN', name: 'China' },
  { code: 'SG', name: 'Singapore' },
  { code: 'AE', name: 'UAE' },
  { code: 'AU', name: 'Australia' },
  { code: 'OTHER', name: 'Other' },
];

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'ILS', symbol: '₪', name: 'Israeli Shekel' },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
];

// Emission factor estimates (kg CO2e)
const EF_ESTIMATES = {
  // Flights: per passenger-km
  flight_short_economy: 0.255,
  flight_short_business: 0.382,
  flight_long_economy: 0.195,
  flight_long_business: 0.566,
  flight_long_first: 0.780,
  flight_spend: 0.30, // per USD
  // Hotels: per night
  hotel_night: 31.1, // Global average
  hotel_spend: 0.25, // per USD
  // Other travel: per km
  rail: 0.035,
  taxi: 0.21,
  rental_car: 0.17,
  bus: 0.089,
  metro: 0.029,
  ferry: 0.19,
  travel_spend: 0.15, // per USD for ground transport
};

interface BusinessTravelFormProps {
  periodId: string;
  onSuccess?: () => void;
}

export function BusinessTravelForm({ periodId, onSuccess }: BusinessTravelFormProps) {
  const goBack = useWizardStore((s) => s.goBack);
  const resetWizard = useWizardStore((s) => s.reset);
  const createActivity = useCreateActivity(periodId);
  const flightDistanceCalc = useFlightDistance();

  // Travel type selection (tabs)
  const [travelType, setTravelType] = useState<TravelType>('flights');

  // Flight fields
  const [flightMethod, setFlightMethod] = useState<CalcMethod>('distance');
  const [originAirport, setOriginAirport] = useState('');
  const [destAirport, setDestAirport] = useState('');
  const [cabinClass, setCabinClass] = useState('economy');
  const [tripType, setTripType] = useState('round_trip');
  const [passengers, setPassengers] = useState(1);
  const [flightDistance, setFlightDistance] = useState<number | null>(null);

  // Flight distance calculator state
  const [distanceCalcResult, setDistanceCalcResult] = useState<{
    origin: string;
    destination: string;
    distance: number;
    haulType: string;
    originName: string;
    destName: string;
  } | null>(null);
  const [distanceCalcError, setDistanceCalcError] = useState<string | null>(null);

  // Hotel fields
  const [hotelMethod, setHotelMethod] = useState<CalcMethod>('physical');
  const [nights, setNights] = useState(1);
  const [rooms, setRooms] = useState(1);
  const [hotelCountry, setHotelCountry] = useState('IL');

  // Other travel fields
  const [otherMethod, setOtherMethod] = useState<CalcMethod>('distance');
  const [otherTravelType, setOtherTravelType] = useState('taxi');
  const [otherDistance, setOtherDistance] = useState<number | null>(null);

  // Common fields
  const [spendAmount, setSpendAmount] = useState<number | null>(null);
  const [currency, setCurrency] = useState('USD');
  const [description, setDescription] = useState('');
  const [travelerName, setTravelerName] = useState('');
  const [activityDate, setActivityDate] = useState(new Date().toISOString().split('T')[0]);

  // Handle flight distance calculation
  const handleCalculateDistance = async () => {
    if (originAirport.length !== 3 || destAirport.length !== 3) {
      setDistanceCalcError('Please enter valid 3-letter IATA airport codes');
      return;
    }

    setDistanceCalcError(null);
    setDistanceCalcResult(null);

    try {
      const result = await flightDistanceCalc.mutateAsync({
        origin: originAirport,
        destination: destAirport,
        cabinClass,
      });

      setFlightDistance(Math.round(result.distance_km));
      setDistanceCalcResult({
        origin: result.origin.iata_code,
        destination: result.destination.iata_code,
        distance: Math.round(result.distance_km),
        haulType: result.haul_type,
        originName: `${result.origin.name} (${result.origin.city})`,
        destName: `${result.destination.name} (${result.destination.city})`,
      });
    } catch (error: any) {
      setDistanceCalcError(error.message || 'Airport not found. Please check the codes.');
    }
  };

  // Calculate estimated emissions
  const estimatedEmissions = useMemo(() => {
    if (travelType === 'flights') {
      if (flightMethod === 'spend' && spendAmount) {
        return spendAmount * EF_ESTIMATES.flight_spend;
      }
      if (flightMethod === 'distance' && flightDistance) {
        const cabin = CABIN_CLASSES.find(c => c.key === cabinClass);
        const trip = TRIP_TYPES.find(t => t.key === tripType);
        const baseEf = flightDistance > 3700
          ? (cabinClass === 'first' ? EF_ESTIMATES.flight_long_first
             : cabinClass === 'business' ? EF_ESTIMATES.flight_long_business
             : EF_ESTIMATES.flight_long_economy)
          : (cabinClass === 'business' ? EF_ESTIMATES.flight_short_business
             : EF_ESTIMATES.flight_short_economy);
        return flightDistance * baseEf * passengers * (trip?.multiplier || 1);
      }
    }

    if (travelType === 'hotels') {
      if (hotelMethod === 'spend' && spendAmount) {
        return spendAmount * EF_ESTIMATES.hotel_spend;
      }
      if (hotelMethod === 'physical' && nights) {
        return nights * rooms * EF_ESTIMATES.hotel_night;
      }
    }

    if (travelType === 'other') {
      if (otherMethod === 'spend' && spendAmount) {
        return spendAmount * EF_ESTIMATES.travel_spend;
      }
      if (otherMethod === 'distance' && otherDistance) {
        const travel = OTHER_TRAVEL_TYPES.find(t => t.key === otherTravelType);
        return otherDistance * (travel?.ef || 0.15);
      }
    }

    return null;
  }, [
    travelType, flightMethod, hotelMethod, otherMethod,
    flightDistance, passengers, cabinClass, tripType,
    nights, rooms, otherDistance, otherTravelType, spendAmount
  ]);

  // Build activity payload
  const buildPayload = () => {
    const basePayload = {
      scope: 3,
      category_code: '3.6',
      activity_date: activityDate,
    };

    if (travelType === 'flights') {
      if (flightMethod === 'spend') {
        return {
          ...basePayload,
          activity_key: 'travel_spend_air',
          quantity: spendAmount,
          unit: 'USD',
          description: description || `Air travel - ${travelerName || 'Business trip'}`,
        };
      }
      // Distance-based
      const isLongHaul = (flightDistance || 0) > 3700;
      let activityKey = 'flight_long_economy';
      if (cabinClass === 'first') activityKey = 'flight_long_first';
      else if (cabinClass === 'business') activityKey = isLongHaul ? 'flight_long_business' : 'flight_short_business';
      else if (cabinClass === 'premium_economy') activityKey = isLongHaul ? 'flight_long_premium_economy' : 'flight_short_economy';
      else activityKey = isLongHaul ? 'flight_long_economy' : 'flight_short_economy';

      const tripMultiplier = tripType === 'round_trip' ? 2 : 1;
      return {
        ...basePayload,
        activity_key: activityKey,
        quantity: (flightDistance || 0) * passengers * tripMultiplier,
        unit: 'passenger-km',
        description: description || `Flight ${originAirport}-${destAirport} (${cabinClass}, ${passengers} pax)`,
      };
    }

    if (travelType === 'hotels') {
      if (hotelMethod === 'spend') {
        return {
          ...basePayload,
          activity_key: 'travel_spend_hotel',
          quantity: spendAmount,
          unit: 'USD',
          description: description || `Hotel - ${travelerName || 'Business trip'}`,
        };
      }
      return {
        ...basePayload,
        activity_key: 'hotel_night',
        quantity: nights * rooms,
        unit: 'nights',
        description: description || `Hotel stay - ${nights} nights, ${rooms} room(s)`,
      };
    }

    if (travelType === 'other') {
      const travelTypeMap: Record<string, string> = {
        rail: otherMethod === 'spend' ? 'travel_spend_rail' : 'rail_domestic_km',
        taxi: otherMethod === 'spend' ? 'travel_spend_taxi' : 'taxi_km',
        rental_car: otherMethod === 'spend' ? 'travel_spend_car_rental' : 'rental_car_km',
        bus: otherMethod === 'spend' ? 'travel_spend_bus' : 'bus_km',
        metro: otherMethod === 'spend' ? 'travel_spend_rail' : 'rail_domestic_km',
        ferry: otherMethod === 'spend' ? 'travel_spend_general' : 'ferry_km',
      };

      if (otherMethod === 'spend') {
        return {
          ...basePayload,
          activity_key: travelTypeMap[otherTravelType] || 'travel_spend_general',
          quantity: spendAmount,
          unit: 'USD',
          description: description || `${OTHER_TRAVEL_TYPES.find(t => t.key === otherTravelType)?.label || 'Travel'} - ${travelerName || 'Business'}`,
        };
      }
      return {
        ...basePayload,
        activity_key: travelTypeMap[otherTravelType] || 'rental_car_km',
        quantity: otherDistance,
        unit: 'km',
        description: description || `${OTHER_TRAVEL_TYPES.find(t => t.key === otherTravelType)?.label || 'Travel'} - ${otherDistance} km`,
      };
    }

    return basePayload;
  };

  const isValid = () => {
    if (travelType === 'flights') {
      if (flightMethod === 'spend') return spendAmount && spendAmount > 0;
      return flightDistance && flightDistance > 0 && passengers > 0;
    }
    if (travelType === 'hotels') {
      if (hotelMethod === 'spend') return spendAmount && spendAmount > 0;
      return nights > 0 && rooms > 0;
    }
    if (travelType === 'other') {
      if (otherMethod === 'spend') return spendAmount && spendAmount > 0;
      return otherDistance && otherDistance > 0;
    }
    return false;
  };

  const handleSave = async (addAnother = false) => {
    if (!isValid()) return;

    const payload = buildPayload();
    await createActivity.mutateAsync(payload as any);

    if (addAnother) {
      // Reset form but keep travel type
      setDescription('');
      setTravelerName('');
      setSpendAmount(null);
      setFlightDistance(null);
      setOriginAirport('');
      setDestAirport('');
      setOtherDistance(null);
    } else {
      resetWizard();
      onSuccess?.();
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Business Travel</h2>
          <p className="text-sm text-foreground-muted">Category 3.6 - Record flights, hotels, and other travel</p>
        </div>
        <Button variant="ghost" size="sm" onClick={goBack}>
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </Button>
      </div>

      {/* Travel Type Tabs */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setTravelType('flights')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            travelType === 'flights'
              ? 'border-primary text-primary'
              : 'border-transparent text-foreground-muted hover:text-foreground'
          }`}
        >
          <Plane className="w-4 h-4" />
          Flights
        </button>
        <button
          onClick={() => setTravelType('hotels')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            travelType === 'hotels'
              ? 'border-primary text-primary'
              : 'border-transparent text-foreground-muted hover:text-foreground'
          }`}
        >
          <Building2 className="w-4 h-4" />
          Hotels
        </button>
        <button
          onClick={() => setTravelType('other')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
            travelType === 'other'
              ? 'border-primary text-primary'
              : 'border-transparent text-foreground-muted hover:text-foreground'
          }`}
        >
          <Car className="w-4 h-4" />
          Other Travel
        </button>
      </div>

      {/* Flights Form */}
      {travelType === 'flights' && (
        <div className="space-y-4">
          {/* Method Selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Calculation Method</label>
            <div className="flex gap-2">
              <button
                onClick={() => setFlightMethod('distance')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  flightMethod === 'distance'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Plane className="w-4 h-4 mx-auto mb-1" />
                Distance Based
              </button>
              <button
                onClick={() => setFlightMethod('spend')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  flightMethod === 'spend'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Calculator className="w-4 h-4 mx-auto mb-1" />
                Spend Based
              </button>
            </div>
          </div>

          {flightMethod === 'distance' ? (
            <>
              {/* Airport Distance Calculator */}
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg space-y-4">
                <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <MapPin className="w-4 h-4 text-primary" />
                  Airport Distance Calculator
                </div>

                {/* Airport Codes */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">From (IATA Code)</label>
                    <Input
                      type="text"
                      value={originAirport}
                      onChange={(e) => {
                        setOriginAirport(e.target.value.toUpperCase().slice(0, 3));
                        setDistanceCalcResult(null);
                        setDistanceCalcError(null);
                      }}
                      placeholder="TLV"
                      maxLength={3}
                      className="font-mono text-center uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">To (IATA Code)</label>
                    <Input
                      type="text"
                      value={destAirport}
                      onChange={(e) => {
                        setDestAirport(e.target.value.toUpperCase().slice(0, 3));
                        setDistanceCalcResult(null);
                        setDistanceCalcError(null);
                      }}
                      placeholder="LHR"
                      maxLength={3}
                      className="font-mono text-center uppercase"
                    />
                  </div>
                </div>

                {/* Calculate Button */}
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCalculateDistance}
                  disabled={originAirport.length !== 3 || destAirport.length !== 3 || flightDistanceCalc.isPending}
                  className="w-full"
                >
                  {flightDistanceCalc.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Calculator className="w-4 h-4 mr-2" />
                  )}
                  Calculate Distance
                </Button>

                {/* Error Message */}
                {distanceCalcError && (
                  <div className="flex items-start gap-2 p-3 bg-error/10 border border-error/20 rounded-lg text-sm">
                    <AlertCircle className="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
                    <span className="text-error">{distanceCalcError}</span>
                  </div>
                )}

                {/* Success Result */}
                {distanceCalcResult && (
                  <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2 text-sm font-medium text-green-700 mb-2">
                      <CheckCircle className="w-4 h-4" />
                      Distance Calculated
                    </div>
                    <div className="text-sm text-foreground space-y-1">
                      <p className="font-mono">
                        {distanceCalcResult.origin} → {distanceCalcResult.destination}
                      </p>
                      <p className="text-xs text-foreground-muted">
                        {distanceCalcResult.originName}
                      </p>
                      <p className="text-xs text-foreground-muted">
                        → {distanceCalcResult.destName}
                      </p>
                      <p className="mt-2">
                        <span className="text-lg font-bold text-primary">{distanceCalcResult.distance.toLocaleString()} km</span>
                        <span className="text-xs text-foreground-muted ml-2">
                          ({distanceCalcResult.haulType}-haul)
                        </span>
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Distance Input (Manual Override) */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Distance (km)
                  {distanceCalcResult && <span className="text-xs text-foreground-muted ml-2">(auto-filled)</span>}
                </label>
                <Input
                  type="number"
                  value={flightDistance || ''}
                  onChange={(e) => setFlightDistance(e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g., 3500"
                  min={0}
                />
                <p className="text-xs text-foreground-muted mt-1">
                  One-way distance. Use the calculator above or enter manually.
                </p>
              </div>

              {/* Cabin Class */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Cabin Class</label>
                <select
                  value={cabinClass}
                  onChange={(e) => setCabinClass(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  {CABIN_CLASSES.map(c => (
                    <option key={c.key} value={c.key}>{c.label}</option>
                  ))}
                </select>
              </div>

              {/* Trip Type and Passengers */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Trip Type</label>
                  <select
                    value={tripType}
                    onChange={(e) => setTripType(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                  >
                    {TRIP_TYPES.map(t => (
                      <option key={t.key} value={t.key}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Number of Passengers</label>
                  <Input
                    type="number"
                    value={passengers}
                    onChange={(e) => setPassengers(Math.max(1, Number(e.target.value)))}
                    min={1}
                  />
                </div>
              </div>
            </>
          ) : (
            /* Spend Method */
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Spend Amount</label>
                <Input
                  type="number"
                  value={spendAmount || ''}
                  onChange={(e) => setSpendAmount(e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g., 1500"
                  min={0}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  {CURRENCIES.map(c => (
                    <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Hotels Form */}
      {travelType === 'hotels' && (
        <div className="space-y-4">
          {/* Method Selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Calculation Method</label>
            <div className="flex gap-2">
              <button
                onClick={() => setHotelMethod('physical')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  hotelMethod === 'physical'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Building2 className="w-4 h-4 mx-auto mb-1" />
                Room Nights
              </button>
              <button
                onClick={() => setHotelMethod('spend')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  hotelMethod === 'spend'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Calculator className="w-4 h-4 mx-auto mb-1" />
                Spend Based
              </button>
            </div>
          </div>

          {hotelMethod === 'physical' ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Number of Nights</label>
                  <Input
                    type="number"
                    value={nights}
                    onChange={(e) => setNights(Math.max(1, Number(e.target.value)))}
                    min={1}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Number of Rooms</label>
                  <Input
                    type="number"
                    value={rooms}
                    onChange={(e) => setRooms(Math.max(1, Number(e.target.value)))}
                    min={1}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Country</label>
                <select
                  value={hotelCountry}
                  onChange={(e) => setHotelCountry(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  {COUNTRIES.map(c => (
                    <option key={c.code} value={c.code}>{c.name}</option>
                  ))}
                </select>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Spend Amount</label>
                <Input
                  type="number"
                  value={spendAmount || ''}
                  onChange={(e) => setSpendAmount(e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g., 800"
                  min={0}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  {CURRENCIES.map(c => (
                    <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Other Travel Form */}
      {travelType === 'other' && (
        <div className="space-y-4">
          {/* Travel Type Selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Travel Type</label>
            <div className="grid grid-cols-3 gap-2">
              {OTHER_TRAVEL_TYPES.map(t => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.key}
                    onClick={() => setOtherTravelType(t.key)}
                    className={`p-3 rounded-lg border text-sm font-medium transition-colors ${
                      otherTravelType === t.key
                        ? 'bg-primary/10 border-primary text-primary'
                        : 'bg-background border-border text-foreground hover:border-primary/50'
                    }`}
                  >
                    <Icon className="w-4 h-4 mx-auto mb-1" />
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Method Selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Calculation Method</label>
            <div className="flex gap-2">
              <button
                onClick={() => setOtherMethod('distance')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  otherMethod === 'distance'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Car className="w-4 h-4 mx-auto mb-1" />
                Distance Based
              </button>
              <button
                onClick={() => setOtherMethod('spend')}
                className={`flex-1 p-3 rounded-lg border text-sm font-medium transition-colors ${
                  otherMethod === 'spend'
                    ? 'bg-primary/10 border-primary text-primary'
                    : 'bg-background border-border text-foreground hover:border-primary/50'
                }`}
              >
                <Calculator className="w-4 h-4 mx-auto mb-1" />
                Spend Based
              </button>
            </div>
          </div>

          {otherMethod === 'distance' ? (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Distance (km)</label>
              <Input
                type="number"
                value={otherDistance || ''}
                onChange={(e) => setOtherDistance(e.target.value ? Number(e.target.value) : null)}
                placeholder="e.g., 150"
                min={0}
              />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Spend Amount</label>
                <Input
                  type="number"
                  value={spendAmount || ''}
                  onChange={(e) => setSpendAmount(e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g., 200"
                  min={0}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Currency</label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground"
                >
                  {CURRENCIES.map(c => (
                    <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Common Fields */}
      <div className="space-y-4 border-t border-border pt-4">
        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Traveler Name (Optional)</label>
          <Input
            type="text"
            value={travelerName}
            onChange={(e) => setTravelerName(e.target.value)}
            placeholder="e.g., John Smith"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Description (Optional)</label>
          <Input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Client meeting in London"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-1">Date</label>
          <Input
            type="date"
            value={activityDate}
            onChange={(e) => setActivityDate(e.target.value)}
          />
        </div>
      </div>

      {/* Emission Estimate */}
      {estimatedEmissions !== null && (
        <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-primary mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-foreground">Estimated Emissions</h4>
              <p className="text-2xl font-bold text-primary mt-1">
                {formatCO2e(estimatedEmissions)}
              </p>
              <p className="text-xs text-foreground-muted mt-1">
                Estimate based on average emission factors. Final calculation may vary.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => handleSave(true)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Plus className="w-4 h-4 mr-2" />
          )}
          Save & Add Another
        </Button>
        <Button
          className="flex-1"
          onClick={() => handleSave(false)}
          disabled={!isValid() || createActivity.isPending}
        >
          {createActivity.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save
        </Button>
      </div>
    </div>
  );
}

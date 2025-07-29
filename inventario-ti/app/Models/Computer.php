<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Computer extends Model
{
    protected $fillable = [
    'username',
    'hostname',
    'os',
    'ip_local',
    'ip_public',
    'cpu',
    'ram',
    'disk',
];
}

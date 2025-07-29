<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\Computer;

class ComputerController extends Controller
{
    public function store(Request $request)
    {
        $data = $request->validate([
            'username' => 'required|string',
            'hostname' => 'required|string',
            'os'       => 'required|string',
            'ip_local' => 'required|ip',
            'ip_public'=> 'nullable|ip',
            'cpu'      => 'required|string',
            'ram'      => 'required|string',
            'disk'     => 'required|string',
        ]);

        $computer = Computer::create($data);

        return response()->json([
            'success' => true,
            'data' => $computer
        ], 201);
    }
}